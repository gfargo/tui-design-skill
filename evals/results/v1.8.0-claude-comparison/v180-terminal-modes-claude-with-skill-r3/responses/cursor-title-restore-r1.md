You need to undo both changes yourself, on every exit path. `ratatui::restore()` resets raw mode, the alternate screen and cursor visibility. It doesn't touch cursor shape or window title, and the panic hook from `ratatui::init()`/`run()` only calls `restore()`.

## What to send

| State | On startup | On exit |
|---|---|---|
| Cursor shape | Nothing to save. The current shape can't be reliably queried. | `CSI 0 SP q` (crossterm `SetCursorStyle::DefaultUserShape`) |
| Window title | Push the user's title with `CSI 22;0t` before you set yours | Pop it with `CSI 23;0t` |

**Limits to know about:**
- **Cursor:** Windows Terminal, foot and Ghostty treat `0` as "the user's configured cursor." xterm treats it as a blinking block. Only xterm patch 411 and later restore the user's choice, using `CSI 7 SP q`. If your users run xterm, detect it (for example with `$XTERM_VERSION`) and send that instead.
- **Title:** xterm, kitty, foot, iTerm2, Alacritty and tmux keep a title stack. WezTerm, Ghostty and Windows Terminal ignore push and pop, so the stale title stays there. On those terminals you could clear the title on exit (Bubble Tea does this) rather than leave the filename. Don't clear it everywhere, though: clearing after a successful pop would wipe the title you just restored.

## Code

```rust
use std::io::{self, Write};
use ratatui::crossterm::{cursor::SetCursorStyle, execute, terminal::SetTitle};

fn enter_extras(file_name: &str) -> io::Result<()> {
    let mut out = io::stdout();
    out.write_all(b"\x1b[22;0t")?;               // push the user's title
    execute!(out, SetTitle(file_name))
}

/// Best effort: each step runs even if an earlier one fails.
fn reset_extras() {
    let mut out = io::stdout();
    let _ = execute!(out, SetCursorStyle::DefaultUserShape); // CSI 0 SP q
    let _ = out.write_all(b"\x1b[23;0t");        // pop the title
    let _ = out.flush();
}

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;
    // Install before ratatui::run so Ratatui's hook wraps this one:
    // restore() → reset_extras() → color-eyre report.
    let report = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        reset_extras();
        report(info);
    }));

    let path = /* ... */;
    let result = ratatui::run(|terminal| {
        enter_extras(&path)?;
        App::new(path).run(terminal)
    });
    reset_extras();       // normal exit and returned errors
    result
}
```

The installation order matters. If you install your hook after `ratatui::init()`/`run()`, it replaces Ratatui's restoring hook instead of being wrapped by it.

## Other exit paths to check

- **Ctrl+C:** in raw mode it arrives as a key event. Make it quit through the normal return path so `reset_extras()` runs.
- **SIGTERM:** the default handler doesn't unwind Rust code, so neither the hook nor the post-`run` call runs. Turn the signal into a quit event in the loop, for example with `signal-hook` or your async runtime's signal handling.
- **Temporary handoff** (`:!shell`, opening `$EDITOR`, Ctrl+Z suspend): call `reset_extras()` before `restore()`. When you come back, re-enter raw mode and the alternate screen, push and set the title again, re-apply the cursor shape for the current mode, and do a full redraw. Otherwise the shell or child program inherits your bar cursor and title.
- **`panic = "abort"`:** the panic hook still runs, but nothing after it does. That's fine, because the reset happens inside the hook.

## Testing

Unit tests won't catch this. Add a PTY smoke test that enters insert mode and then exits three ways: normally, by Ctrl+C, and by a forced panic. In each case, assert that the captured output ends with `ESC[0 q` and `ESC[23;0t`.
