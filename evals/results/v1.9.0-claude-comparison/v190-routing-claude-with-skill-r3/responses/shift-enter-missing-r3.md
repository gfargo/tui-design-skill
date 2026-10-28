Shift+Enter can't reach your app in the legacy key encoding. Both keys send the same byte (`\r`), so your app has nothing to tell apart. Inside tmux the legacy encoding is all you get by default, because tmux's `extended-keys` option is off. So you need a newline key that works everywhere, and Shift+Enter becomes an extra where the terminal supports it.

## 1. Add a newline key that always works

In a chat-style field, Enter sends and a modifier inserts a newline. Bind all three of these:

| Key | Why it works |
|---|---|
| **Ctrl+J** | Sends a line feed (`\n`), which is a different byte from Enter's `\r` even in the legacy encoding. Works in every terminal, every multiplexer, and over SSH. |
| **Alt+Enter** | Arrives as `ESC` + `\r`. Most terminals send it, and so does tmux. |
| **`\` then Enter** | If the line ends in a backslash, remove it and insert a newline. This works even if a terminal swallows Alt. |

State the key in the placeholder or footer, for example `Enter send · Ctrl+J newline`. Otherwise nobody will find it.

## 2. Turn Shift+Enter on where the terminal supports it

Shift+Enter becomes its own key once the kitty keyboard protocol is on (push flags with `CSI > 1 u`, pop them with `CSI < u` on exit). kitty, Ghostty, WezTerm (with `enable_kitty_keyboard`), foot, Alacritty 0.13+, iTerm2 and Windows Terminal 1.25+ support it. What your framework does:

- **Bubble Tea v2:** turns it on by default. Always accept both `shift+enter` and `ctrl+j`. Only show the Shift+Enter hint after `tea.KeyboardEnhancementsMsg` arrives with `SupportsKeyDisambiguation()` true. That message may come after the first frame, or not at all.
- **Ratatui / crossterm:** off by default. Check `supports_keyboard_enhancement()`, then push `KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES`. You also have to pop the flags yourself on every exit path, panics included, and while still on the alternate screen. Ratatui's `restore()` won't do it.
- **Textual:** on by default.
- **Ink 8:** opt-in through the `kittyKeyboard` option on `render()`. Pastel 4 can't pass it, so call `render()` yourself.

## 3. tmux needs extra configuration

Even with the protocol on, tmux sends the legacy encoding unless the user configures it. If you want Shift+Enter there, document something like this in your README:

```tmux
set -s extended-keys on                          # or 'always'
set -as terminal-features 'xterm*:extkeys'       # tell tmux the outer terminal supports it
# tmux 3.5+: set -s extended-keys-format csi-u
```

Restart the tmux server afterward. Some caveats:
- tmux's extended keys use xterm's `modifyOtherKeys`/CSI u style, which is not the full kitty protocol.
- With `on`, tmux only sends extended keys to apps that ask for them. Bubble Tea asks through `modifyOtherKeys`. A crossterm app that only pushes kitty flags may still get nothing, which is when `always` helps.
- The `terminal-features` pattern has to match the outer terminal's `TERM`.

You can't count on users editing their `tmux.conf`, which is why the fallbacks in step 1 are the real fix.

## Two related checks

- **Paste:** turn on bracketed paste (`CSI ? 2004 h`) so pasted newlines go into the field and never submit. Without it, kitty and Ghostty turn a pasted newline into Enter.
- **Testing:** write a unit test that sends `ctrl+j`, `alt+enter` and a trailing `\` + Enter to your update logic and checks that each inserts `\n`. Then do one manual check inside tmux with default settings.

If you tell me your framework, I can write the exact key-handling code for your input component.
