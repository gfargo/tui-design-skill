Restore both things on every exit path, and restore them to what the user had before, not to values you hardcode. (There's no Rust code in this directory, so this is general guidance rather than a patch.)

## 1. Cursor shape: reset to the user's default, not to a block

Send `DECSCUSR 0` (`CSI 0 SP q`). In crossterm that's `SetCursorStyle::DefaultUserShape`. It tells the terminal to go back to the cursor shape the user configured. Don't use `SteadyBlock`: someone who normally uses an underline or blinking cursor would be left with the wrong shape again. Also send `Show` in case the cursor was hidden.

## 2. Title: push it on startup, pop it on exit

You usually can't read the current title back. The query sequence (`CSI 21 t`) is disabled in most terminals for security reasons. Use the xterm title stack instead:

- **Before you first set a title:** `CSI 22;0 t` saves the current title.
- **On exit:** `CSI 23;0 t` restores it.

xterm, kitty, foot, WezTerm, VTE-based terminals and tmux support this. Terminals that don't simply ignore it. In those, the user's shell prompt usually resets the title anyway. Don't fall back to setting an empty title or a guess, because that just replaces one stale title with another.

## 3. Cover every exit path

`ratatui::restore()` only turns off raw mode and leaves the alternate screen. It doesn't touch the cursor shape or the title, so you need your own restore function and you need to call it from:

- **Normal quit and `?` error returns:** use a `Drop` guard.
- **Panics:** chain a panic hook that calls your restore and then the previous hook.
- **SIGTERM/SIGHUP:** restore, then exit. Ctrl-C arrives as a key event while in raw mode, so it goes through your normal quit path.
- **Suspend (Ctrl-Z / SIGTSTP):** restore before stopping. On SIGCONT, re-enter the alternate screen, push the title again, set it, and reapply the cursor shape for the current mode.

```rust
use std::io::{self, Write};
use crossterm::{cursor::{SetCursorStyle, Show}, execute};

pub fn enter_tui() -> io::Result<()> {
    let mut out = io::stdout();
    out.write_all(b"\x1b[22;0t")?; // push title
    // ... enable raw mode, EnterAlternateScreen, SetTitle(filename) ...
    out.flush()
}

pub fn restore_terminal() {
    let mut out = io::stdout();
    // Ignore errors: this runs from Drop/panic paths and must not fail halfway.
    let _ = execute!(out, SetCursorStyle::DefaultUserShape, Show);
    let _ = out.write_all(b"\x1b[23;0t"); // pop title
    let _ = ratatui::restore(); // raw mode off + leave alternate screen
    let _ = out.flush();
}

struct TerminalGuard;
impl Drop for TerminalGuard {
    fn drop(&mut self) { restore_terminal(); }
}

pub fn install_panic_hook() {
    let prev = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        restore_terminal();
        prev(info);
    }));
}
```

Things to watch:

- **Pushes and pops must match.** Pop exactly once for each push. If restore can run twice (for example from the panic hook and then from `Drop`), use a flag so the second call does nothing.
- **Order:** restore the cursor and title before leaving the alternate screen and turning off raw mode, so the panic message prints to a normal terminal.
- **If you use `ratatui::init()`:** it installs its own panic hook, so install yours afterwards so it wraps that one.
