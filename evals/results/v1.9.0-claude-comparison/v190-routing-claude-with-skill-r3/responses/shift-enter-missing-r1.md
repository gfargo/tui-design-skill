The fix is to stop depending on Shift+Enter alone. Give the field a newline key that every terminal can send, and treat Shift+Enter as a bonus where the terminal can report it.

## Why it happens

In the standard (legacy) key encoding, Shift+Enter and Enter send the same byte, a carriage return (`\r`). Your app isn't dropping the Shift; the information never arrives. Shift+Enter only becomes its own key when the terminal uses an enhanced keyboard protocol, such as the kitty keyboard protocol or xterm's `modifyOtherKeys`, and the app turns it on.

tmux makes this worse. It sits between the terminal and your app, and its `extended-keys` option is **off by default**. So even if your terminal (kitty, Ghostty, WezTerm, iTerm2…) can tell the two keys apart, tmux passes your app the plain legacy version.

## What to do

**1. Bind a newline key that always works.**

| Key | Why it works |
|---|---|
| `Ctrl+J` | Sends a line feed (`\n`), which is different from Enter's carriage return (`\r`) even in the legacy encoding. This is the most reliable option. |
| `Alt+Enter` | Arrives as Esc followed by `\r`, so you can detect it. It gets the Esc-timing issue below, so don't make it the only route. |
| `\` then `Enter` | A trailing backslash means "continue on the next line". This works everywhere and is easy to discover. |

In tmux, a lone Esc is delayed by the `escape-time` setting (500 ms before tmux 3.5, 10 ms after). On older tmux that can split an Alt key into a separate Esc and Enter. That's another reason `Ctrl+J` should be the main fallback.

**2. Accept Shift+Enter when the terminal can report it.** Turn on keyboard enhancement, and always accept `shift+enter` alongside the fallbacks. Only *show* Shift+Enter in your hints once the terminal confirms it supports enhancement:
- **Bubble Tea v2:** it already requests the kitty protocol and `modifyOtherKeys`. Check `tea.KeyboardEnhancementsMsg` and `msg.SupportsKeyDisambiguation()` before showing the hint, because that message may arrive after the first frame or not at all.
- **crossterm / Ratatui:** this is off by default. Push `KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES`, and pop it yourself on every exit path, panics included. Ratatui's `restore()` doesn't undo it. Pop it before leaving the alternate screen, because terminals keep a separate keyboard-mode stack for each screen.
- **Textual:** it enables the kitty protocol automatically.
- **Ink:** you have to opt in.

**3. Tell users the newline key.** Put it in the placeholder or footer, and don't advertise a key that might not work:
```
Enter send · Ctrl+J newline
```
Switch the hint to `Shift+Enter newline` once enhancement is confirmed.

**4. Document the tmux setting for users who want real Shift+Enter:**
```tmux
set -g extended-keys on                       # or 'always'
set -as terminal-features 'xterm*:extkeys'    # match your outer $TERM
```
This is a starting point, not something I've tested. What tmux forwards depends on its version and on which protocol your app requests, so try it on your target tmux version. Your app should still work without it, because most users won't change their tmux.conf.

## Two related checks

- **Bracketed paste:** turn it on (`CSI ? 2004 h`), so newlines in pasted text are inserted instead of acting like Enter and sending a half-written message. A paste should never submit.
- **Editor-style fields** (long text rather than chat) can flip the convention: Enter inserts a newline and `Ctrl+S` sends. Ctrl+Enter has the same legacy-encoding problem as Shift+Enter, so don't make it the only way to send.

If you tell me your framework, I can write the exact key handling and teardown code for it.
