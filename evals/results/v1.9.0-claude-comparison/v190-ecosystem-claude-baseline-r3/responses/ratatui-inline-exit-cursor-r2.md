There's no code in this directory, so this answer is based on how Ratatui behaves, not on your files.

## Why each version went wrong

**`ratatui::run` takes over the whole screen.** It calls `ratatui::init()`, which switches to the alternate screen and uses a fullscreen viewport. `run` doesn't take viewport options, so for an inline UI you have to set up the terminal yourself with `init_with_options`.

**The prompt landed on your UI's last line.** With an inline viewport there's no alternate screen to leave on exit. Your UI stays in the normal scrollback, and the cursor stays wherever the last frame left it, which is inside your UI. When your program exits, the shell prints its prompt at that cursor position.

## Fix

```rust
use ratatui::{TerminalOptions, Viewport};

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;

    // Turns on raw mode but stays on the normal screen, with a 10-row area
    // under the prompt. If the cursor is near the bottom, the terminal
    // scrolls up to make room. Also installs a panic hook that restores the terminal.
    let mut terminal = ratatui::init_with_options(TerminalOptions {
        viewport: Viewport::Inline(10),
    });

    let result = run(&mut terminal);   // your event loop -> Result<Option<PathBuf>>

    // Erase the picker and put the cursor back where the UI started.
    // Do this even if run() failed, so the terminal is never left messy.
    let _ = terminal.clear();
    ratatui::restore();                // turns off raw mode, shows the cursor

    if let Some(path) = result? {
        println!("{}", path.display());
    }
    Ok(())
}
```

For an inline viewport, `terminal.clear()` moves the cursor to the top-left corner of the UI area and clears everything after it. The shell prompt (or your printed path) then appears exactly where the picker was, with nothing left over.

### If you want the picker to stay visible after exit

Don't clear. Instead, move the cursor to the UI's last row and print a newline so the prompt starts below it:

```rust
let area = terminal.get_frame().area();
terminal.set_cursor_position((0, area.bottom() - 1))?;
ratatui::restore();
println!();
```

### If you build the terminal by hand

Do the same steps `init_with_options` does, but leave out `EnterAlternateScreen`:

```rust
crossterm::terminal::enable_raw_mode()?;
let backend = CrosstermBackend::new(std::io::stdout());
let mut terminal = Terminal::with_options(backend, TerminalOptions {
    viewport: Viewport::Inline(10),
})?;
// ... loop ...
terminal.clear()?;
crossterm::terminal::disable_raw_mode()?;
terminal.show_cursor()?;
```

You'll also need to install your own panic hook that disables raw mode. Without one, a panic leaves the shell in raw mode.

## One thing to watch for with pickers

If you plan to use it as `vim "$(mypicker)"`, the shell captures stdout, so a UI drawn to stdout never shows up. In that case, build the terminal by hand with `CrosstermBackend::new(std::io::stderr())` (or write to `/dev/tty`). Keep stdout only for printing the selected path. `init_with_options` always draws to stdout, so it won't work for this.
