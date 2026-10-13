**Recommendation:** Ratatui won't clean these up for you. `ratatui::restore()` (and `ratatui::run`) only undo raw mode and the alternate screen. The cursor shape and window title are things your app turned on, so your app has to turn them off, on every exit path:

1. **Cursor:** on exit, send DECSCUSR 0 (`CSI 0 SP q`). Crossterm calls this `SetCursorStyle::DefaultUserShape`. Terminals give no reliable way to read the current shape, so you can't save it and put it back. Resetting to the default is the best available option.
2. **Title:** save the user's title before you set your own, and restore it on exit. Push it onto the terminal's title stack with `CSI 22;0 t` before the first `SetTitle`, and pop it with `CSI 23;0 t` on exit. Crossterm has no command for push or pop, so write the bytes yourself.

### Implementation

Put both steps in a drop guard inside the managed lifecycle. It then runs on a normal quit, on a `?` error return, and during a panic unwind (after Ratatui's panic hook has restored the terminal):

```rust
use std::io::{self, Write};
use ratatui::crossterm::{cursor::SetCursorStyle, execute};

/// Terminal state we change ourselves, which ratatui::restore() doesn't undo.
struct TermExtras;

impl TermExtras {
    fn enter() -> io::Result<Self> {
        let mut out = io::stdout();
        out.write_all(b"\x1b[22;0t")?; // push the user's title before we set ours
        out.flush()?;
        Ok(Self)
    }
}

impl Drop for TermExtras {
    fn drop(&mut self) {
        let mut out = io::stdout();
        let _ = execute!(out, SetCursorStyle::DefaultUserShape); // CSI 0 SP q
        let _ = out.write_all(b"\x1b[23;0t");                     // pop the title
        let _ = out.flush();
    }
}

fn main() -> color_eyre::Result<()> {
    color_eyre::install()?;
    ratatui::run(|terminal| {
        let _extras = TermExtras::enter()?;
        App::default().run(terminal) // sets SetTitle(file name) and bar/block per mode
    })
}
```

### Cases that need extra handling

- **`panic = "abort"`:** if your Cargo profile sets this, the guard's `Drop` never runs. Do the same reset in a panic hook installed *before* `ratatui::run`/`init`. Ratatui wraps that hook, so it restores the terminal first and then calls yours.
- **SIGTERM:** Rust doesn't unwind on SIGTERM by default, so no cleanup code runs. Turn the signal into a quit event in your event loop so the program exits through the guard. SIGKILL can't be handled at all.
- **Handing off to a child process** (`:!shell`, external editor, Ctrl+Z): reset the cursor to `DefaultUserShape` before handing over the terminal. When you resume, re-apply the shape for the current mode, along with re-entering raw mode, reloading, and redrawing. Otherwise the shell or child starts with your bar cursor.

### Terminal limitations

- **Title stack support:** xterm, kitty, foot, iTerm2, Alacritty and tmux support the push/pop stack. WezTerm, Ghostty and Windows Terminal ignore it, so the user's original title can't be restored there. The pop does no harm on those terminals, but the title stays stale until something else sets it. If that matters, a fallback is to clear the title (`OSC 2 ;` with an empty string) on terminals you detect as lacking the stack. That's what Bubble Tea does on exit.
- **xterm and DECSCUSR 0:** xterm reads `CSI 0 SP q` as a blinking block, not the user's configured cursor. Only xterm patch 411 and later restore the user's choice, using `CSI 7 SP q`. Windows Terminal, foot and Ghostty treat 0 as the user's default.

### Test it

Add a small PTY smoke test that captures the output bytes for four cases: normal quit, an error return, a panic, and SIGTERM. Assert that each ends with `ESC[0 q` and `ESC[23;0t`. This is a lifecycle bug, so unit tests and frame snapshots won't catch it.
