You need two changes. Start the terminal with `ratatui::init_with_options` and `Viewport::Inline(n)`, because `ratatui::run` always uses the alternate screen. Then move the cursor off the UI's last line before you restore the terminal.

## Why it happens

- **Full screen:** `ratatui::run()` and `ratatui::init()` always enter the alternate screen. `ratatui::init_with_options` turns on raw mode and installs the panic hook, but doesn't enter the alternate screen. With `Viewport::Inline(n)`, it reserves `n` rows below the prompt instead.
- **Prompt on your last line:** with an inline viewport, the last frame stays on screen. The cursor is left at the end of its last cell, so the next thing the shell prints joins that line. `Terminal::clear()` doesn't fix this on its own because it puts the cursor back where it was. You have to move the cursor yourself.

## The fix

```rust
use ratatui::{backend::Backend, Terminal, TerminalOptions, Viewport};

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;                       // before Ratatui wraps the panic hook
    let options = TerminalOptions { viewport: Viewport::Inline(10) };
    let mut terminal = ratatui::init_with_options(options); // raw mode + panic hook, no alt screen
    let result = Picker::default().run(&mut terminal);      // keep the result; don't `?` yet
    let _ = erase_inline(&mut terminal);          // remove the picker, park the cursor
    ratatui::restore();                           // runs on every non-panic path
    if let Some(path) = result? {
        println!("{}", path.display());
    }
    Ok(())
}

/// Erase a transient UI and leave the cursor where it began.
fn erase_inline<B: Backend>(terminal: &mut Terminal<B>) -> Result<(), B::Error> {
    let origin = terminal.get_frame().area().as_position();
    terminal.clear()?;
    terminal.set_cursor_position(origin)
}
```

Other points:

- **Draw into `frame.area()`**, not `Rect::new(0, 0, ..)`. The viewport starts wherever the cursor was, not at row 0.
- **Erase or keep:** a picker usually should vanish, so call `erase_inline`. If you'd rather leave the last frame in scrollback, skip that call and print an empty line with `println!()` after `restore()`.
- **Keep the run result until cleanup is done.** If you use `?` on the run loop's result before restoring, an error skips cleanup and leaves the terminal in raw mode.
- **Printing above the picker:** for status lines that should stay, use `terminal.insert_before(1, |buf| ...)`. Turn on Ratatui's `scrolling-regions` feature so the viewport isn't cleared and redrawn each time.

## If the selected path goes to stdout (`cd "$(pick)"`)

A summon-and-choose tool should draw its UI on stderr (or `/dev/tty`) and print only the result on stdout. `init_with_options` draws to stdout, so inside `$(...)` the UI would be captured along with the path. I also believe `ratatui::restore()` writes a leave-alternate-screen sequence to stdout, which would end up in the captured result too; I haven't checked that against the source. In that case, build the terminal yourself on stderr and only turn raw mode off:

```rust
use std::io::stderr;
use ratatui::{
    backend::CrosstermBackend,
    crossterm::terminal::{disable_raw_mode, enable_raw_mode},
    Terminal, TerminalOptions, Viewport,
};

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;
    let report = std::panic::take_hook();         // a hand-built terminal gets no hook for free
    std::panic::set_hook(Box::new(move |info| {
        let _ = disable_raw_mode();
        eprintln!();                              // get off the UI's last line
        report(info);
    }));

    enable_raw_mode()?;
    let mut terminal = Terminal::with_options(
        CrosstermBackend::new(stderr()),
        TerminalOptions { viewport: Viewport::Inline(10) },
    )?;
    let result = Picker::default().run(&mut terminal);
    let _ = erase_inline(&mut terminal);
    disable_raw_mode()?;

    if let Some(path) = result? {
        println!("{}", path.display());           // only the result goes to stdout
    }
    Ok(())
}
```

## Things to check

- **Exit paths:** check Enter, Esc, Ctrl+C, an error, and a forced panic. After each one, the prompt should start on a fresh line and typing should echo normally (raw mode is off).
- **Near the bottom of the screen:** run it with the prompt on the bottom row. Ratatui should scroll up to make room for the 10 rows, and erasing should still leave the cursor where the picker started.
- **Captured output:** `x=$(pick); printf '%q\n' "$x"` should show a plain path with no escape sequences.
- **Extra modes:** if you turn on mouse capture or bracketed paste, turn them off before `restore()` and in the panic hook. `restore()` only handles raw mode and the alternate screen.
