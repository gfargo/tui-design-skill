`ratatui::run(...)` uses the default fullscreen setup, including the alternate screen. For an inline picker, create a terminal with `Viewport::Inline(height)` and manage raw mode yourself. **Do not enter the alternate screen.**

With the Crossterm backend, the lifecycle looks like this:

```rust
use std::io::{self, Write};

use crossterm::terminal::{disable_raw_mode, enable_raw_mode};
use ratatui::{
    backend::CrosstermBackend,
    Terminal, TerminalOptions, Viewport,
};

fn main() -> io::Result<()> {
    enable_raw_mode()?;

    let setup = Terminal::with_options(
        CrosstermBackend::new(io::stdout()),
        TerminalOptions {
            viewport: Viewport::Inline(10),
        },
    );

    let mut terminal = match setup {
        Ok(terminal) => terminal,
        Err(error) => {
            let _ = disable_raw_mode();
            return Err(error);
        }
    };

    // Your draw/event loop. Return errors instead of exiting the process.
    let result = run_picker(&mut terminal);

    // Raw mode and cursor visibility alone don't put the prompt below the UI.
    let area = terminal.get_frame().area();
    let position = terminal.set_cursor_position((
        0,
        area.bottom().saturating_sub(1),
    ));
    let raw = disable_raw_mode();
    let cursor = terminal.show_cursor();

    // Move onto a fresh line; this also scrolls if we're at the screen bottom.
    let newline = (|| -> io::Result<()> {
        let mut stdout = io::stdout();
        stdout.write_all(b"\r\n")?;
        stdout.flush()
    })();

    // Cleanup was attempted even if the picker returned an error.
    result?;
    position?;
    raw?;
    cursor?;
    newline
}
```

`run_picker` represents your existing application loop.

Two details matter:

- Draw using **`frame.area()`**, which describes the inline viewport. Its `y` coordinate may be nonzero.
- Before returning to the shell, **move to the viewport’s last row and emit a newline**. Restoring raw mode and showing the cursor does not advance it, which is why your prompt appeared inside the UI.

This preserves the final picker display in scrollback. If you want it erased, call `terminal.clear()` during cleanup before positioning the cursor. For panic cleanup, add a panic hook or an RAII guard that restores raw mode and cursor visibility.