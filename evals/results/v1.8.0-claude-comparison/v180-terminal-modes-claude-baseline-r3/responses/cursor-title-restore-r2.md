Restore both on every exit path. Ratatui's built-in `ratatui::restore()` only leaves the alternate screen and disables raw mode. It doesn't touch cursor shape or window title, so you need to handle those two yourself.

## 1. Cursor shape: reset to the user's default, not to a block

Send `DECSCUSR 0` (`CSI 0 SP q`). In crossterm that's `SetCursorStyle::DefaultUserShape`. Don't use `SteadyBlock`. Some users configure an underline or blinking cursor, and code 0 gives them back whatever their terminal is configured to use.

## 2. Title: save it on startup, restore it on exit

A terminal app can't reliably read the current title, so you can't capture it and set it back later. Instead, use xterm's title stack:

- On startup, before setting your own title: `CSI 22;0 t` saves the current title.
- On exit: `CSI 23;0 t` restores the saved title.

xterm, kitty, WezTerm, foot, Alacritty, VTE-based terminals and tmux support this. Terminals that don't support it ignore the sequence, which is harmless. Crossterm has no command for it, so write the bytes directly. Many shells also reset the title at each prompt, which covers the remaining cases.

## 3. Cover every exit path

A stale cursor or title usually means one of these paths was missed:

- normal quit
- an error returned through `?`
- a panic
- `SIGTERM` / `SIGHUP`
- `Ctrl-Z` (restore on suspend, re-apply your cursor and title on `SIGCONT`)

```rust
use std::io::{self, Write};
use crossterm::{cursor::{SetCursorStyle, Show}, execute,
    terminal::{disable_raw_mode, LeaveAlternateScreen}};

const PUSH_TITLE: &[u8] = b"\x1b[22;0t";
const POP_TITLE:  &[u8] = b"\x1b[23;0t";

pub fn init() -> io::Result<ratatui::DefaultTerminal> {
    io::stdout().write_all(PUSH_TITLE)?;          // before any SetTitle
    let hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let _ = restore();                         // restore first so the panic message is readable
        hook(info);
    }));
    Ok(ratatui::init())
}

pub fn restore() -> io::Result<()> {
    let mut out = io::stdout();
    execute!(out, SetCursorStyle::DefaultUserShape, Show, LeaveAlternateScreen)?;
    disable_raw_mode()?;
    out.write_all(POP_TITLE)?;
    out.flush()
}

// Drop guard so `?` and early returns still restore
pub struct TerminalGuard;
impl Drop for TerminalGuard {
    fn drop(&mut self) { let _ = restore(); }
}
```

For signals, a crate like `signal-hook` can set a flag that your event loop checks. The loop then exits normally and the guard runs. Don't call `restore()` directly from inside a signal handler.

## Notes

- **Restore only what you changed.** Don't clear the title or call `SetTitle("")` as a fallback, because that wipes out the user's own title. If you never pushed a title, don't pop one.
- **Restore is idempotent.** The panic hook and the drop guard can both run, and running `restore()` twice is harmless.
- **Test it.** Quit normally, with a forced panic, with `kill <pid>`, and with Ctrl-Z then `fg`. Check the result inside tmux too.

If you point me at your terminal setup and teardown code, I can show exactly where this fits.
