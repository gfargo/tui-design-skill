The working directory is empty, so this answer is based on how tmux and terminals behave, not on your code. Both problems come from tmux.

## 1. Ctrl+B does nothing

**Ctrl+B is tmux's default prefix key.** tmux catches it and waits for a follow-up command key, so your app never receives it. You can't fix this from inside your app. Asking users to rebind their tmux prefix isn't reasonable, and GNU screen has the same problem with **Ctrl+A**.

**Design rules:**
- **Don't use Ctrl+B or Ctrl+A as default shortcuts.** In practice, avoid most bare Ctrl+letter combos for important actions anyway. Many are already taken:
  - **Ctrl+C, Ctrl+Z, Ctrl+\\** are signals.
  - **Ctrl+S and Ctrl+Q** are XON/XOFF flow control unless you turn on raw mode / `-ixon`.
  - **Ctrl+H** is Backspace, **Ctrl+I** is Tab, **Ctrl+M** is Enter and **Ctrl+[** is Esc. Terminals send identical bytes for each pair.
- **Use keys that reach your app reliably**, for example:
  - Vim-style leader sequences: `Space e`, or `g s` in normal mode.
  - Function keys.
  - A command palette, e.g. `:` or Ctrl+P.
- **Make every binding user-configurable**, and document known clashes (tmux, screen, Zellij's Ctrl+P/Ctrl+O, etc.).
- **Detect multiplexers** with `$TMUX`, `$STY` or `$ZELLIJ`. When one is present you could pick other defaults or show a one-time hint.
- **Give every keyboard action a second way in**: a menu, the command palette, or a mouse click on the sidebar edge. Then a swallowed shortcut is never a dead end.

## 2. Esc feels laggy

Terminals have no separate "Escape key" event. Pressing Esc sends the byte `0x1b`, and that same byte starts every escape sequence: arrow keys (`ESC [ A`), Alt+key (`ESC x`), and so on. When the program reading input sees a bare `0x1b`, it has to wait briefly to find out whether more bytes are coming.

**tmux adds a wait of its own.** Its `escape-time` setting defaults to 500 ms (newer releases lower it to 10 ms). Then your app or library waits again: ncurses `ESCDELAY` defaults to 1000 ms, and many frameworks use 25–100 ms. The two delays add up, so leaving insert mode lags.

**What to do:**
- **In your app:** keep your own Esc-disambiguation timeout short, about 10–50 ms. With ncurses, call `set_escdelay(25)` or set `ESCDELAY`. Most frameworks have an equivalent setting.
- **Use the kitty keyboard protocol where available** (CSI u / "progressive enhancement", sent as `CSI > 1 u`). With it, Esc arrives as an unambiguous sequence, so no timeout is needed, and Ctrl+I can be told apart from Tab, and so on. kitty, WezTerm, foot, Ghostty and recent iTerm2 support it. tmux has partial support via `extended-keys`. Query for support and fall back cleanly if it's missing.
- **For users:** document the fix in a "Running inside tmux" section:
  ```tmux
  set -sg escape-time 10
  ```
  You can also detect `$TMUX`, run `tmux show -sv escape-time`, and show a warning if it's large. Neovim's `:checkhealth` does exactly this.
- **Offer other ways out of insert mode**, like Vim does: **Ctrl+[** (the same byte, so it has the same delay, but users expect it), Ctrl+C, or a configurable `jk` / `jj` chord. These avoid the timeout completely.

## Summary

| Problem | Cause | Fix |
|---|---|---|
| Ctrl+B ignored | tmux prefix catches it | Pick a different default; make bindings configurable; add a palette or menu |
| Esc lag | tmux `escape-time` plus your app's Esc timeout | Short app timeout; kitty keyboard protocol; detect and warn about tmux `escape-time`; alternative exit keys |

As a general rule, treat everything outside your app (tmux, screen, the terminal emulator, the OS) as able to swallow or delay keys. Choose defaults with that in mind, and never make a single key the only way to reach a feature.
