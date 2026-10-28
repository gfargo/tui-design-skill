Use `ratatui::init_with_options` with `Viewport::Inline(height)`. `ratatui::run()` and `init()` enter the alternate screen, which explains the full-screen takeover.

For a transient picker, clear its viewport **and move the cursor back to its origin** before restoring the terminal:

```rust
use ratatui::{DefaultTerminal, TerminalOptions, Viewport};

fn main() -> std::io::Result<()> {
    let mut terminal = ratatui::init_with_options(TerminalOptions {
        viewport: Viewport::Inline(8),
    });

    // Keep the result: `?` here would skip normal cleanup.
    let result = run_picker(&mut terminal);

    let origin = terminal.get_frame().area().as_position();
    let cleared = terminal.clear();
    let positioned = terminal.set_cursor_position(origin);

    ratatui::restore();

    result?;
    cleared?;
    positioned?;
    Ok(())
}

fn run_picker(terminal: &mut DefaultTerminal) -> std::io::Result<()> {
    // Your event loop:
    // terminal.draw(|frame| {
    //     frame.render_widget(..., frame.area());
    // })?;
    // ...
    Ok(())
}
```

Two details matter:

- Draw relative to **`frame.area()`**, because an inline viewport can begin partway down the screen.
- `Terminal::clear()` alone restores the old cursor position. Explicitly returning to the viewport origin prevents the next shell prompt from appearing on the UI’s last line.

If you want to **keep the final frame**, omit the clear/reposition steps and call `println!()` **after** `ratatui::restore()` to put the shell prompt on a fresh line.

`init_with_options` manages raw mode and installs Ratatui’s panic cleanup hook. If you enable mouse capture, bracketed paste, or keyboard enhancement modes yourself, also disable those on normal and panic exits.

For a picker used in pipelines, keep UI output on stderr or `/dev/tty` and emit only the selected path on stdout; the default terminal setup above writes its UI to stdout.