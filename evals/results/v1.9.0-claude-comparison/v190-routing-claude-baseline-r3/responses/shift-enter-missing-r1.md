There's no code in this directory, so this answer is general. The short version: in a classic terminal, Shift+Enter and Enter both send the same byte (`\r`), so the Shift is gone before your app sees anything. tmux adds a second layer that drops it again. You have two options: turn on an extended keyboard protocol through the whole chain, or accept a fallback key that already sends something different.

## 1. Check what actually arrives

Run `cat -v` (or `od -c`), inside and outside tmux, and press Enter and then Shift+Enter:

- `^M` both times: the modifier is lost.
- `^[[13;2u` (CSI u / kitty) or `^[[27;2;13~` (modifyOtherKeys): it's working.

## 2. Make every layer pass it through

**a) Your TUI has to request extended keys.** Terminals don't send them unless asked:

```
\x1b[>4;2m    # xterm modifyOtherKeys level 2  (works through tmux)
\x1b[>1u      # kitty keyboard protocol, push flags (direct terminals)
```

On exit or suspend, undo them with `\x1b[>4;0m` / `\x1b[<u`. Your parser then needs to treat `CSI 13;2u` and `CSI 27;2;13~` as Shift+Enter. Many libraries handle this for you: crossterm (`PushKeyboardEnhancementFlags`), Textual, Bubble Tea v2, notcurses, libtickit/termkey.

**b) tmux (3.2+) needs this in `~/.tmux.conf`:**

```tmux
set -s extended-keys on            # or 'always' to send them even if the app didn't ask
set -as terminal-features 'xterm*:extkeys'
# tmux 3.5+: pick the format sent to apps
set -s extended-keys-format csi-u
```

After that, run `tmux kill-server` (just re-sourcing the config isn't always enough). tmux speaks modifyOtherKeys and CSI u to the apps inside it, but it doesn't pass the kitty protocol through. Inside tmux, request modifyOtherKeys (`\x1b[>4;2m`).

**c) The outer terminal also has to send it:**

| Terminal | Setting |
|---|---|
| iTerm2 | Profiles → Keys → "Report keys using CSI u" (or Shift+Enter → Send Escape Sequence `[13;2u`) |
| kitty, Ghostty, foot | supported natively |
| WezTerm | `enable_kitty_keyboard = true` or `enable_csi_u_key_encoding = true` |
| Alacritty | supports kitty protocol (0.13+); or bind `Shift+Enter` → `chars = "\u001b[13;2u"` |
| macOS Terminal.app | not supported, so use a fallback |

## 3. Fallbacks that work everywhere (support these anyway)

Users will run your TUI in setups you don't control, so accept at least one of these as "insert newline":

- **Alt/Option+Enter** sends `ESC \r`. On macOS, Option needs to be set to send Meta/Esc+.
- **Ctrl+J** sends `\n` (0x0A), while Enter sends `\r` (0x0D) in raw mode. They're different bytes with no setup needed.
- **`\` then Enter** works as a line continuation.
- **Bracketed paste** (`\x1b[?2004h`) keeps pasted newlines from submitting.

My recommendation: support Ctrl+J and Alt+Enter right away, add CSI u / modifyOtherKeys parsing for Shift+Enter, and mention the tmux `extended-keys` lines in your docs.
