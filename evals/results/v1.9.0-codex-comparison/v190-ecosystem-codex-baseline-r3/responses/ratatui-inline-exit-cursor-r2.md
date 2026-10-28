`ratatui::run(...)` uses the fullscreen setup. For an inline picker, create a terminal with `Viewport::Inline(height)` and **don’t enter the alternate screen**.

On exit, move the cursor below the viewport as well as restoring terminal modes. Showing the cursor alone leaves it inside your last frame, which is why the shell prompt overlaps it.

```rust
use std::io::{self, stdout};

use ratatui::{
    backend::CrosstermBackend,
    crossterm::{
        cursor::{MoveToNextLine, Show},
        execute,
        terminal::{disable_raw_mode, enable_raw_mode},
    },
    Terminal, TerminalOptions, Viewport,
};

fn main() -> io::Result<()> {
    enable_raw_mode()?;

    let terminal = Terminal::with_options(
        CrosstermBackend::new(stdout()),
        TerminalOptions {
            viewport: Viewport::Inline(10),
        },
    );

    let mut terminal = match terminal {
        Ok(terminal) => terminal,
        Err(err) => {
            let _ = disable_raw_mode();
            return Err(err);
        }
    };

    // Save the result so an error doesn't skip cleanup.
    let result = run_picker(&mut terminal);

    // Use the viewport's current position: it may have moved on resize.
    let area = terminal.get_frame().area();
    let cursor_result =
        terminal.set_cursor_position((area.x, area.bottom().saturating_sub(1)));

    let raw_result = disable_raw_mode();
    // Also works at the screen bottom, where it scrolls one line.
    let exit_result = execute!(terminal.backend_mut(), Show, MoveToNextLine(1));

    result?;
    cursor_result?;
    raw_result?;
    exit_result
}
```

Here `run_picker` is your existing draw/event loop returning `io::Result<()>`.

This keeps the final picker visible and places the next shell prompt beneath it. If you want the picker erased, call `terminal.clear()` before positioning the exit cursor.

Also install panic cleanup or use a cleanup guard if you build the terminal yourself: the code above restores the terminal on ordinary errors, but a panic skips that cleanup.