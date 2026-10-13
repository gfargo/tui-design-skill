## Why it happens

In the legacy key encoding, **Shift+Enter and Enter send the same byte (`\r`)**. The terminal drops the Shift modifier before your app sees anything, so no binding in Bubble Tea can tell the two apart.

Bubble Tea v2 asks the terminal for extended keys at startup: the kitty keyboard protocol's "disambiguate" flag, plus xterm `modifyOtherKeys`. Then it depends on where the app is running:

- **kitty, Ghostty, foot, Alacritty 0.13+, WezTerm (with `enable_kitty_keyboard`), Windows Terminal 1.25+:** they accept the request and send Shift+Enter as its own escape sequence. You get a `tea.KeyPressMsg` with `Mod: tea.ModShift`, so your binding works.
- **Terminals without the protocol** (macOS Terminal.app, older xterm-likes, many IDE terminals): they ignore the request and you get a plain `\r`, which your app reads as Enter and sends the message.
- **tmux:** tmux sits between you and the real terminal and re-encodes every key. Its `extended-keys` option is off by default, so it sends you the legacy encoding even when the outer terminal is kitty. Zellij and GNU screen have similar issues.

This isn't a bug you can fix in the app. Shift+Enter is an accelerator that only exists when every layer between the keyboard and your app supports extended keys.

## Recommended design

Don't make Shift+Enter the only way to insert a newline. Keep Enter as send, keep Shift+Enter where it works, and always offer a newline key that survives the legacy encoding.

1. **Enter sends.** It works everywhere.
2. **Newline keys, in this order:**
   - **Shift+Enter:** when the terminal supports it.
   - **Ctrl+J:** the main fallback. In raw mode Enter sends CR (`0x0D`) and Ctrl+J sends LF (`0x0A`), so they stay distinct in every terminal, in tmux, and over SSH. Also bind it as an alias in kitty so one key works everywhere.
   - **Alt+Enter:** a second alias (it arrives as `ESC` + `\r`). It's unreliable as the only fallback: macOS Terminal and iTerm2 need "Option as Meta" turned on, Windows Terminal uses Alt+Enter for fullscreen, and Zellij takes many Alt keys.
   - **Optional: `\` then Enter** turns a trailing backslash into a newline instead of sending. People know it from shells, and it works with any keyboard.
3. **Make the hint match what actually works.** Bubble Tea reports whether the terminal accepted the keyboard enhancements. Show `shift+enter newline` when disambiguation is on, and `ctrl+j newline` when it isn't. If the hint advertises Shift+Enter in a terminal where it sends, users get the exact bug you're seeing.
4. **Pasted text never sends.** Bubble Tea v2 turns on bracketed paste by default. Insert multi-line pastes as text and make sure a newline in a paste never reaches your send handler.
5. **Document the tmux setup.** For users who want Shift+Enter inside tmux:
   ```tmux
   set -s extended-keys on
   set -as terminal-features 'xterm*:extkeys'
   ```
   The outer terminal also has to support extended keys. Treat this as an optional extra, since Ctrl+J already works there.

## Bubble Tea v2 sketch

The Bubbles `textarea` binds newline to Enter by default, so rebind it and handle send yourself before the textarea sees the key:

```go
keys := textarea.DefaultKeyMap()
keys.InsertNewline = key.NewBinding(
    key.WithKeys("shift+enter", "ctrl+j", "alt+enter"),
    key.WithHelp("ctrl+j", "newline"),
)
m.input.KeyMap = keys

// Update
case tea.KeyboardEnhancementsMsg:
    m.shiftEnterOK = msg.SupportsKeyDisambiguation()
    m.refreshHints() // "shift+enter newline" vs "ctrl+j newline"

case tea.KeyPressMsg:
    if msg.String() == "enter" { // plain Enter only; shift+enter falls through
        if strings.HasSuffix(m.input.Value(), `\`) { /* trim \, insert newline */ }
        return m, m.send()
    }
```

The general pattern (accelerator plus legacy fallback) comes from the skill. These API names are from my own knowledge of v2, not the skill: `KeyboardEnhancementsMsg`, `SupportsKeyDisambiguation`, and the textarea `KeyMap.InsertNewline` field. Check them against your pinned Bubble Tea and Bubbles versions.

## Tests

Unit-test `Update` with key literals, no terminal needed:
- `tea.KeyPressMsg{Code: tea.KeyEnter}` sends.
- `tea.KeyPressMsg{Code: tea.KeyEnter, Mod: tea.ModShift}` inserts a newline.
- `tea.KeyPressMsg{Code: 'j', Mod: tea.ModCtrl}` inserts a newline.
- A multi-line paste message inserts text and doesn't send.

Then check by hand in kitty, in plain tmux (only Ctrl+J and Alt+Enter should insert a newline, and the hint should say `ctrl+j`), in tmux with `extended-keys on`, and in macOS Terminal.app.
