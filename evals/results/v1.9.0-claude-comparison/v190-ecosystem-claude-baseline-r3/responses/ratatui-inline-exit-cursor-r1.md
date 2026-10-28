I don't see your code in the working directory, so this answer is based on how Ratatui works rather than your source.

## Why each attempt failed

1. **`ratatui::run` takes the whole screen.** It calls `ratatui::init()`, which turns on raw mode, switches to the alternate screen and uses a fullscreen viewport. `run` has no options, so you can't use it for an inline UI.
2. **The prompt lands on your UI's last line.** The shell prints its prompt wherever the cursor is when your program exits. In inline mode, the cursor is still inside the viewport, usually on the last line drawn. Nothing moved it out, so the prompt printed over your UI. A hand-built terminal also has no panic hook, so a panic leaves raw mode on.

## Fix

Use `init_with_options` with an inline viewport. Before restoring, choose where the cursor should end up:

```rust
use ratatui::{TerminalOptions, Viewport};

fn main() -> std::io::Result<()> {
    // Inline viewport, 12 rows tall, drawn under the prompt. No alternate screen.
    // Also installs a panic hook that restores the terminal.
    let mut terminal = ratatui::init_with_options(TerminalOptions {
        viewport: Viewport::Inline(12),
    });

    let result = App::default().run(&mut terminal);

    // Erase the picker. The cursor returns to the viewport's top-left,
    // so the next prompt appears where the picker started.
    terminal.clear()?;
    ratatui::restore(); // turns off raw mode

    // Print after restore. In raw mode, "\n" doesn't return to column 0.
    if let Ok(Some(path)) = &result {
        println!("{}", path.display());
    }
    result.map(|_| ())
}
```

If you'd rather leave the final frame on screen than erase it, skip `clear()`. Instead, put the cursor on the viewport's last row and print a newline after restoring:

```rust
let area = terminal.get_frame().area();
terminal.set_cursor_position((0, area.bottom().saturating_sub(1)))?;
ratatui::restore();
println!(); // moves below the UI; the prompt goes there
```

## If the shell captures the picker's output

If you run it as `vim "$(picker)"` or bind it to a key in zsh, the shell captures stdout. Ratatui's escape codes would then end up in the captured output. To avoid that, draw the UI on stderr and print only the selected path to stdout:

```rust
use ratatui::{backend::CrosstermBackend, Terminal, TerminalOptions, Viewport};

crossterm::terminal::enable_raw_mode()?;
let mut terminal = Terminal::with_options(
    CrosstermBackend::new(std::io::stderr()),
    TerminalOptions { viewport: Viewport::Inline(12) },
)?;
// ... run app ...
terminal.clear()?;
crossterm::terminal::disable_raw_mode()?;
println!("{}", path.display()); // only this goes to stdout
```

With this hand-built setup, you need your own panic hook that calls `disable_raw_mode()` before the default hook runs. That's the part `init_with_options` would otherwise handle for you.
