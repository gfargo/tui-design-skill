The core issue is that cursor shape and window title belong to the terminal, not to your app's screen. Leaving the alternate screen restores the buffer contents but leaves both of those as you set them. Ratatui's `ratatui::restore()` won't fix this either: it only disables raw mode and leaves the alternate screen. You have to undo both changes yourself, on every way the program can exit.

I didn't find the terminal setup code in this directory, so this is general guidance rather than a patch.

## 1. Cursor: reset to the user's default, not to a block

Send `SetCursorStyle::DefaultUserShape` (the escape code `CSI 0 SP q`). This tells the terminal to go back to whatever cursor the user has configured. Don't send `BlinkingBlock` or `SteadyBlock`: that replaces the user's preference with yours, which is a smaller version of the same bug. Also send `Show` in case the cursor was hidden.

## 2. Title: save it at startup, restore it at exit

You can't read the current title back; most terminals turn off that query for security reasons. Instead, use xterm's title stack:

- **At startup**, before setting any title: `CSI 22;0 t` saves the current title.
- **At exit**: `CSI 23;0 t` restores it.

xterm, kitty, WezTerm, foot, Alacritty and most modern terminals support this. Terminals that don't simply ignore it. In those, the title stays stale until the user's shell prompt sets it again, which most shells do anyway. Don't try to fix that by setting an empty title, because it can wipe out the shell's title.

## 3. Restore on every exit path

```rust
use std::io::{self, stdout, Write};
use crossterm::{cursor::{SetCursorStyle, Show}, execute};

const PUSH_TITLE: &[u8] = b"\x1b[22;0t";
const POP_TITLE: &[u8] = b"\x1b[23;0t";

pub fn init() -> io::Result<ratatui::DefaultTerminal> {
    let mut out = stdout();
    out.write_all(PUSH_TITLE)?;
    out.flush()?;
    let terminal = ratatui::init(); // installs ratatui's panic hook

    // Chain our own restore in front of ratatui's hook.
    let prev = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        restore_extras();
        prev(info);
    }));
    Ok(terminal)
}

/// Undo terminal state that ratatui::restore() doesn't touch.
fn restore_extras() {
    let mut out = stdout();
    let _ = execute!(out, SetCursorStyle::DefaultUserShape, Show);
    let _ = out.write_all(POP_TITLE);
    let _ = out.flush();
}

pub fn restore() {
    restore_extras();
    ratatui::restore();
}
```

Make sure every exit path runs this:

- **Normal quit:** call `restore()`. You can also put it in a `Drop` guard so early `?` returns are covered. `Drop` doesn't run on `std::process::exit` or with `panic = "abort"`, which is why the panic hook is also needed.
- **Panics:** the chained hook above handles these.
- **Signals (SIGTERM, SIGHUP):** if you handle them, for example with `signal-hook`, restore and then exit.
- **Suspend (Ctrl‑Z) and shelling out** (`:!cmd`, `$EDITOR`, a pager): restore before handing over the terminal. When you resume, push the title again and re-apply your title and cursor shape.

Make the restore code safe to run twice, since the guard and the hook may both fire. The worst case is that the title stack gets popped twice, which is harmless. If you want to be strict about it, add an `AtomicBool`.
