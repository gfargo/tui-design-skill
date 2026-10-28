There's no Rust code in the working directory, so this answer is based on how Ratatui behaves rather than on your files. Both problems have clear causes and short fixes.

## Why it happens

1. **Full screen:** `ratatui::run()` calls `ratatui::init()`. That turns on raw mode and switches to the **alternate screen** with a `Viewport::Fullscreen`. `run` doesn't take viewport options, so for inline mode you have to set up the terminal yourself.
2. **Prompt on your UI's last line:** In inline mode, Ratatui leaves the cursor wherever it last drew, which is inside the viewport. When you restore the terminal, the shell prints its prompt at that cursor position. You need to move the cursor yourself before restoring.

## Fix: inline viewport, then clear or step past it

```rust
use ratatui::{TerminalOptions, Viewport};

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;

    // Raw mode, no alternate screen, 12-line region under the prompt.
    // Also installs a panic hook that restores the terminal.
    let mut terminal = ratatui::init_with_options(TerminalOptions {
        viewport: Viewport::Inline(12),
    });

    let result = App::default().run(&mut terminal);

    // Option A (picker style, like fzf --height): erase the UI.
    // For inline viewports, clear() moves the cursor to the viewport's
    // top-left and clears everything after it, so the prompt comes back
    // where the picker started.
    let _ = terminal.clear();

    ratatui::restore(); // disable raw mode, show cursor

    // Print the selection *after* restoring, on a clean line.
    if let Ok(Some(path)) = &result {
        println!("{}", path.display());
    }
    result.map(|_| ())
}
```

If you'd rather **leave the final UI visible** (Option B), replace `terminal.clear()` with this:

```rust
let area = terminal.get_frame().area();
let _ = terminal.set_cursor_position((0, area.bottom().saturating_sub(1)));
ratatui::restore();
println!(); // move to the line below the UI; scrolls if it's at the bottom
```

Don't set the cursor to `area.bottom()` directly. When the viewport sits at the bottom of the screen, that row is off-screen, which is why the code uses the last row plus a newline.

Two details:
- Restore the terminal even if `run` returned an error. That's why the code stores `result` and propagates it after restoring, instead of using `?` inside the setup.
- Inline mode doesn't use the alternate screen, so don't call `EnterAlternateScreen` anywhere in a hand-built setup. If you do, you'll get full-screen behavior again.

## If you'll use it as `cd "$(picker)"`

With command substitution, stdout is a pipe, so a UI drawn to stdout gets captured instead of shown. `init_with_options` always uses stdout. To handle this, draw the UI to **stderr** (or `/dev/tty`) and print only the result to stdout, which is what fzf does:

```rust
use crossterm::terminal::{disable_raw_mode, enable_raw_mode};
use ratatui::{backend::CrosstermBackend, Terminal, TerminalOptions, Viewport};

enable_raw_mode()?;
let mut terminal = Terminal::with_options(
    CrosstermBackend::new(std::io::stderr()),
    TerminalOptions { viewport: Viewport::Inline(12) },
)?;

let result = App::default().run(&mut terminal);

let _ = terminal.clear();
let _ = terminal.show_cursor();
disable_raw_mode()?;

if let Ok(Some(path)) = &result {
    println!("{}", path.display()); // stdout → captured by $(...)
}
```

This setup doesn't install `init`'s panic hook, so add your own hook that calls `disable_raw_mode()`. Otherwise a panic will leave the shell in raw mode.
