You need three changes. Start with `ratatui::init_with_options` and `Viewport::Inline(n)` in place of `ratatui::run`. Before restoring the terminal, either erase the picker or move the cursor to a new line. And if the picker will run inside `$(...)`, draw the UI on stderr.

## Why it happened

- **Whole screen:** `ratatui::run()` and `ratatui::init()` always switch to the alternate screen. They have no inline option.
- **Prompt on your last line:** after an inline viewport exits, the last frame stays on screen and the cursor sits at the end of its last cell. The shell prints its prompt right there. `terminal.clear()` doesn't fix this, because it puts the cursor back where it was. You have to move it to the viewport's origin yourself.

## The fix

```rust
use ratatui::{backend::Backend, Terminal, TerminalOptions, Viewport};

fn main() -> std::io::Result<()> {
    // Raw mode and the panic hook, but no alternate screen.
    // Reserves 12 rows below the prompt.
    let options = TerminalOptions { viewport: Viewport::Inline(12) };
    let mut terminal = ratatui::init_with_options(options);

    let result = run(&mut terminal);          // your event loop; returns Option<PathBuf>
    let _ = erase_inline(&mut terminal);      // remove the picker
    ratatui::restore();

    if let Ok(Some(path)) = &result {
        println!("{}", path.display());       // the answer, on a clean line
    }
    result.map(|_| ())
}

/// Erase the inline UI and put the cursor back where the picker started.
fn erase_inline<B: Backend>(terminal: &mut Terminal<B>) -> Result<(), B::Error> {
    let origin = terminal.get_frame().area().as_position();
    terminal.clear()?;
    terminal.set_cursor_position(origin)
}
```

There are two clean ways to exit:
1. **Erase, then print** (above). This is how fzf works: the picker disappears and only the result is left.
2. **Keep the last frame as a receipt.** Skip `erase_inline` and call `println!()` after `restore()`, so the prompt starts on a new line under the UI. Use this only if the last frame is useful afterward. Never leave a half-drawn picker on screen.

**In your draw code,** draw into `frame.area()`, not `Rect::new(0, 0, …)`. The viewport starts wherever the cursor was when you launched, which is usually not row 0.

**Lines that should stay** (status messages, "copied …") go through `terminal.insert_before(1, |buf| Line::from(msg).render(buf.area, buf))`. They print above the picker and scroll into normal scrollback. Turn on Ratatui's `scrolling-regions` feature so this doesn't clear and redraw the viewport each time.

## If it runs in `$(...)`, draw on stderr

`init_with_options` draws on stdout. With `vim "$(mypicker)"`, the captured value would then include all of the UI's escape codes. For a picker, the UI should go to stderr (or `/dev/tty`) and only the chosen path to stdout. That means building the terminal yourself, which also makes you responsible for cleanup and panics:

```rust
use ratatui::{backend::CrosstermBackend, crossterm::terminal::{enable_raw_mode, disable_raw_mode}};

let report_hook = std::panic::take_hook();
std::panic::set_hook(Box::new(move |info| {
    let _ = disable_raw_mode();
    report_hook(info);
}));

enable_raw_mode()?;
let backend = CrosstermBackend::new(std::io::stderr());
let mut terminal = Terminal::with_options(backend, TerminalOptions { viewport: Viewport::Inline(12) })?;

let result = run(&mut terminal);
let _ = erase_inline(&mut terminal);
let _ = terminal.show_cursor();
let _ = disable_raw_mode();
// then println! the selection to stdout
```

Don't add this `restore()`-style hook on top of `ratatui::run()` or `init*()`, because those already install one. You only need it when you set the terminal up by hand. Also, `ratatui::restore()` resets stdout, so in the stderr version undo each mode yourself, as shown.

## Check it in a real terminal

- Quit normally, cancel with Esc or Ctrl+C, return an error, and force a panic. Each time the prompt should come back on its own line, with the cursor visible and the terminal out of raw mode (typed text shows up).
- Launch near the bottom of the screen. The terminal should scroll to make room for the 12 rows, and erasing should still leave the cursor in the right place.
- Run `x=$(mypicker); printf %q "$x"` and confirm `x` holds only the path, with no escape codes.

I based this on the skill's Ratatui *Inline viewport* section and its rule for inline pickers: UI on stderr, answer on stdout, erase on exit. I haven't run the code against your project. The stderr version follows that rule, but the skill's Rust reference has no stderr example for it, so test that path.
