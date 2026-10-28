Shift+Enter usually can't reach your app at all. In the legacy key encoding, Shift+Enter and Enter send the same byte (`\r`), so your input field has nothing to tell them apart. That's why it looks identical. You get Shift+Enter only after the terminal switches to an enhanced keyboard protocol. tmux adds a second problem: its `extended-keys` option is off by default, so even a terminal that supports the protocol has the modifier stripped before your app sees it.

So the fix is to make sure newline insertion never depends on Shift+Enter, then add Shift+Enter as an extra shortcut where it works.

## 1. Bind newline keys that work everywhere

In a chat-style field, where Enter sends:

| Key | Why it works |
|---|---|
| **Ctrl+J** | Sends a line feed (`\n`), which differs from Enter's carriage return (`\r`) even in the legacy encoding. It's the most reliable option. |
| **Alt+Enter** | Arrives as `ESC \r`, which is distinguishable, though Alt can be taken by Zellij or the terminal's own keybindings. |
| **`\` then Enter** | If the line ends in a backslash, swap it for a newline instead of submitting. It needs no modifier, so it works over SSH, in screen, and anywhere else. |
| **Shift+Enter** | Accept it whenever it arrives, but treat it as a shortcut on top of the others. |

Show the newline key in the placeholder or footer, e.g. `Enter send · Ctrl+J newline`. Show "Shift+Enter" in that hint only after the terminal confirms keyboard enhancement. Otherwise you're advertising a key that does nothing.

If your field is editor-like instead, flip it: Enter inserts a newline and Ctrl+Enter or Ctrl+S sends. Ctrl+Enter has the same protocol limits as Shift+Enter, so Ctrl+S is the safer fallback.

Also turn on bracketed paste (`CSI ? 2004 h`). Without it, a pasted newline arrives as Enter and submits the message halfway through.

## 2. Turn on the keyboard protocol outside tmux

Push the kitty keyboard protocol with `CSI > 1 u` (flag 1, "disambiguate") and pop it with `CSI < u` on every exit path. With it on, Shift+Enter arrives as its own key. kitty, Ghostty, foot, WezTerm (with `enable_kitty_keyboard`), iTerm2, Alacritty 0.13+, and Windows Terminal 1.25+ support it. Detect support with `CSI ? u` and treat a missing reply as "not supported".

What each framework does by default:
- **Bubble Tea v2:** on by default. Bind `shift+enter` and `ctrl+j` together, and gate the hint on `KeyboardEnhancementsMsg` → `SupportsKeyDisambiguation()`.
- **crossterm / Ratatui:** off by default. Push `PushKeyboardEnhancementFlags(DISAMBIGUATE_ESCAPE_CODES)` yourself. Ratatui's `restore()` doesn't undo it, so pop it in your own teardown, including on panic.
- **Textual:** on by default.
- **Ink:** opt-in.

## 3. Get it through tmux

tmux sits between your app and the terminal and forwards extended keys only when configured to. In `~/.tmux.conf`:

```tmux
set -s extended-keys on
set -as terminal-features 'xterm*:extkeys'   # adjust the pattern to your outer $TERM
# tmux 3.5+: choose the format tmux sends to apps
set -s extended-keys-format csi-u
```

Then **restart the tmux server** (`tmux kill-server`). Reloading the config doesn't renegotiate with a client that's already attached.

Two caveats:
- With `extended-keys on`, tmux sends extended keys only to apps that ask for them. tmux understands xterm's `modifyOtherKeys` request (`CSI > 4 ; 2 m`), and Bubble Tea sends it alongside the kitty push. If you write raw sequences, send it too, and reset it with `CSI > 4 ; 0 m` on exit.
- These lines live in the *user's* tmux.conf, which you don't control. Put them in your docs, and keep the Ctrl+J path from step 1, because most tmux users will never add them.

## Quick check

1. Log raw input bytes to a file (never to the screen your TUI is drawing on).
2. Press Shift+Enter outside tmux, then inside it.
3. A bare `0d` means the modifier was lost. If you get an escape sequence instead, such as `ESC [ 13 ; 2 u` or `ESC [ 27 ; 2 ; 13 ~`, Shift+Enter is coming through and your key handler just needs to map it.

If you tell me your framework (Bubble Tea, Ratatui, Textual, Ink, prompt_toolkit…), I can write the exact binding and teardown code.
