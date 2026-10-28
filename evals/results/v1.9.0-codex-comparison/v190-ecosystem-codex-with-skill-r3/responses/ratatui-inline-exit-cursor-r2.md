Use **`init_with_options` with `Viewport::Inline(n)`**. `ratatui::run()` and `init()` enter the alternate screen, which is why they take over the terminal.

For a transient picker, clear its viewport **and move the cursor back to its origin** before restoring terminal modes:

```rust
use std::io;
use ratatui::{
    backend::Backend, Terminal, TerminalOptions, Viewport,
};

fn main() -> io::Result<()> {
    let mut terminal = ratatui::init_with_options(TerminalOptions {
        viewport: Viewport::Inline(8),
    });

    let result = run_picker(&mut terminal); // your existing event loop
    let cleanup = erase_inline(&mut terminal);

    // Restore even when the picker or cleanup returned an error.
    ratatui::restore();

    result?;
    cleanup
}

fn erase_inline<B: Backend>(
    terminal: &mut Terminal<B>,
) -> Result<(), B::Error> {
    let origin = terminal.get_frame().area().as_position();
    terminal.clear()?;
    terminal.set_cursor_position(origin)
}
```

The prompt overlap is a separate cursor issue: the last frame leaves the cursor on its last line. **`clear()` alone restores the old cursor position**, so explicitly returning to the viewport origin matters.

A few details:

- Draw within `frame.area()`; an inline viewport may start below row zero.
- To **keep the final frame**, skip `erase_inline()` and print a newline **after `restore()`** so the next prompt starts on a fresh line.
- `init_with_options()` installs Ratatui’s panic restoration hook. Hand-built terminals require your own normal/error/panic cleanup.
- Undo any mouse capture, bracketed paste, or keyboard enhancement modes you enabled; `restore()` does not undo those.
- If the picker outputs a selected path for scripts, put interactive rendering on stderr or `/dev/tty` and reserve stdout for that result.