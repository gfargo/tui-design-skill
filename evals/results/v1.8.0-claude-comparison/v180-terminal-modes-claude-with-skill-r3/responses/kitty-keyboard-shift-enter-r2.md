**Short answer:** this isn't a bug in your code. In the legacy keyboard encoding, Shift+Enter and Enter send the same byte (`\r`), so your app can't tell them apart. Keep Shift+Enter as the nice shortcut where the terminal can report it, and always bind a newline key that works everywhere: **Ctrl+J**, plus **Alt+Enter**.

## Why it works in kitty but not elsewhere

- **Legacy terminals send the same byte.** Without an extended keyboard protocol, Enter, Shift+Enter and Ctrl+M all send carriage return. Bubble Tea gets `enter` with no modifier because the modifier never reaches it.
- **kitty reports the modifier.** Bubble Tea v2 turns on the kitty keyboard protocol's "disambiguate" flag and xterm's `modifyOtherKeys` at startup. Terminals that support one of these send a separate code for Shift+Enter: kitty, Ghostty, foot, WezTerm with `enable_kitty_keyboard`, Alacritty 0.13+, and Windows Terminal 1.25+. Terminals that support neither ignore the request and send a plain `\r`. Terminal.app and many VTE-based terminals fall in this group.
- **tmux removes it.** tmux decodes keys from the outer terminal and re-encodes them for the pane. Its `extended-keys` option is off by default, so even inside kitty, tmux passes Shift+Enter on as a plain `\r`. Users can turn it on:

  ```tmux
  set -s extended-keys on            # or 'always'
  set -as terminal-features 'xterm*:extkeys'
  ```

  Treat this as a tip for your docs, not a requirement. Most users won't have it set.

So "Shift+Enter inserts a newline" can only ever be an extra shortcut. It can't be the only way to get a newline.

## The design

| Action | Binding | Works in |
|---|---|---|
| Send | `enter` | Everywhere |
| Newline | `shift+enter` | Terminals with the kitty protocol or `modifyOtherKeys`, and tmux with `extended-keys` on |
| Newline | `ctrl+j` | Everywhere. It sends a line feed (`\n`), which is a different byte from Enter's `\r` |
| Newline | `alt+enter` | Almost everywhere (it sends ESC then `\r`). On macOS the Option key must be set to act as Meta |
| Multi-line paste | Bracketed paste | Inserts the text and never sends it |

Rules that go with it:

1. **Don't swap it to "Enter = newline, Ctrl+Enter = send."** Ctrl+Enter has the same problem as Shift+Enter, so sending would break in the same terminals.
2. **Only show hints for keys that work.** Bubble Tea v2 sends a `tea.KeyboardEnhancementsMsg` when the terminal confirms enhanced key support. Show `shift+enter newline` only after that. Until then, show `ctrl+j newline`. Show `alt+enter` in the `?` help screen.
3. **Paste must never send.** A pasted newline should go into the text box, not submit the message. In v2, bracketed paste is on by default and arrives as a `tea.PasteMsg`. Make sure the input box receives that message rather than a key handler.
4. **Optional:** a trailing `\` before Enter becomes a newline. Some chat CLIs do this. It's easy to learn and needs no special keys.
5. **Optional:** some users set their terminal (VS Code, iTerm2) to send ESC + `\r` for Shift+Enter. That arrives as `alt+enter`, which your binding already handles, so mention this setting in your docs.

## Bubble Tea v2 sketch

By default the `bubbles/textarea` component treats `enter` as "insert newline", so you need to change that binding. Also handle `enter` yourself before the textarea sees it:

```go
m.input.KeyMap.InsertNewline = key.NewBinding(
    key.WithKeys("shift+enter", "alt+enter", "ctrl+j"),
    key.WithHelp("ctrl+j", "newline"),
)

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyboardEnhancementsMsg:
        m.shiftEnterWorks = msg.SupportsKeyDisambiguation()
        m.input.KeyMap.InsertNewline.SetHelp(m.newlineHint(), "newline")
    case tea.KeyPressMsg:
        if msg.String() == "enter" {
            return m.submit()
        }
    }
    var cmd tea.Cmd
    m.input, cmd = m.input.Update(msg)
    return m, cmd
}
```

Two things the skill reference doesn't cover, so check them against the Bubble Tea version you've pinned:

- The `KeyboardEnhancementsMsg` and `SupportsKeyDisambiguation` names.
- That a bare line feed decodes as `ctrl+j` and not as `enter`.

## Testing

- **Unit tests:** send synthetic key presses to `Update` and check the result:
  - `tea.KeyPressMsg{Code: tea.KeyEnter}` sends.
  - The same key with `Mod: tea.ModShift` inserts a newline.
  - `ctrl+j` and `alt+enter` insert a newline.
  - A `PasteMsg` containing `\n` never sends.
- **Golden test of the footer:** render it before and after the `KeyboardEnhancementsMsg` arrives, so the hint changes correctly.
- **Manual check on real terminals:** a PTY test can't show what a real terminal sends. Check kitty, Terminal.app or GNOME Terminal, and tmux with and without `extended-keys`. The fallback keys should work in all of them, and Shift+Enter should show as a hint only where it works.
