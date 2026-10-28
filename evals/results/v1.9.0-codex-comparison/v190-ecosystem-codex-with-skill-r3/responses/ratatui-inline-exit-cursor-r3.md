Use **`init_with_options` with `Viewport::Inline(n)`**. `ratatui::run()` and `init()` enter the alternate screen, which is why your picker takes over the screen.

For Ratatui 0.30, wrap your existing picker loop like this:

```rust
use ratatui::{DefaultTerminal, TerminalOptions, Viewport};
use std::io;

fn main() -> io::Result<()> {
    let mut terminal = ratatui::init_with_options(TerminalOptions {
        viewport: Viewport::Inline(8),
    });

    // Save the result: `?` here would skip normal cleanup.
    let result = run_picker(&mut terminal);

    // Remove the transient picker and return to its current origin.
    // Capture this after the loop: resizing/scrolling may move it.
    let origin = terminal.get_frame().area().as_position();
    let cleanup = terminal
        .clear()
        .and_then(|()| terminal.set_cursor_position(origin));
    let cursor = terminal.show_cursor();

    ratatui::restore();

    result?;
    cleanup?;
    cursor
}

fn run_picker(terminal: &mut DefaultTerminal) -> io::Result<()> {
    // Your draw/event loop.
    // Always lay out widgets relative to frame.area().
    todo!()
}
```

The shell prompt joining your UI is a **cursor-position problem**: the last frame leaves the cursor on its final line. Choose one exit behavior:

- **Erase the picker:** clear it and move to the viewport origin, as above. `clear()` alone restores the previous cursor position.
- **Keep the final frame:** omit the erase/reposition code and print a newline **after `ratatui::restore()`**, when raw mode is off.

`init_with_options` provides raw-mode setup and a restoration panic hook without entering the alternate screen. A hand-built `Terminal` needs its own normal-error and panic cleanup. Undo any mouse capture, bracketed paste, or keyboard flags you enable yourself.

For a picker used in pipelines, keep interactive rendering on stderr or `/dev/tty`, and write only the selected path to stdout after cleanup.