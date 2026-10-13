**Short answer:** In most terminals, Shift+Enter and Enter send the same byte, a carriage return (`\r`). Your app can't tell them apart, so the Enter binding wins. The keys only become distinct when the terminal speaks the kitty keyboard protocol, or xterm's `modifyOtherKeys`, and the app turns that on. Treat Shift+Enter as an extra shortcut where it works, and always give users a newline key that works everywhere.

## Why kitty works and other terminals don't

- **Without the protocol, the bytes are identical.** Enter sends `\r`, and so does Shift+Enter in iTerm2's defaults, Terminal.app, and the VS Code terminal.
- **Bubble Tea v2 already asks for the better encoding.** On startup it requests the kitty protocol's "disambiguate" flag and `modifyOtherKeys`. Terminals that support either one (kitty, Ghostty, foot, WezTerm with `enable_kitty_keyboard`, Alacritty 0.13+, Windows Terminal 1.25+) send Shift+Enter as its own code, such as `CSI 13;2u`. Your binding then matches. Terminals without support ignore the request and keep sending `\r`.
- **tmux usually blocks it.** tmux sits between the terminal and your app and re-encodes every key. Its `extended-keys` option is off by default, so even inside kitty your app receives plain `\r`. Users can turn it on in `tmux.conf`:
  ```tmux
  set -s extended-keys on
  set -as terminal-features 'xterm*:extkeys'   # tell tmux the outer terminal supports it
  set -s extended-keys-format csi-u            # tmux 3.5+
  ```
  Put those lines in your docs, but don't depend on them. Most users won't have them set, and SSH, screen, and Zellij each change things again.

## The design

Enter sends. Several keys insert a newline, at least one of which works in every terminal:

| Key | Works where | Notes |
|---|---|---|
| **Shift+Enter** | Only where the keys are distinct (see above) | Shortcut; advertise it only when it works |
| **Ctrl+J** | Everywhere | Sends a line feed (`\n`), which differs from Enter's `\r` in raw mode. This is your guaranteed fallback. |
| **Alt+Enter** | Most terminals, tmux included | Sends Esc followed by `\r`. On macOS, Option must be set to act as Meta. |
| `\` then Enter | Everywhere | Optional and easy to discover: a trailing backslash turns Enter into a newline (Claude Code does this) |
| Paste | Everywhere | Bracketed paste is on by default in Bubble Tea v2. Insert pasted newlines as text; never let a paste send the message. |
| Open in `$EDITOR` (e.g. Ctrl+X Ctrl+E) | Everywhere | Optional, for long messages; use `tea.ExecProcess` |

The rules that make this work:

1. **Handle the send key before the textarea sees it.** By default the Bubbles textarea treats Enter as "insert newline", so rebind it.
2. **Detect support instead of guessing from `TERM` or `$TMUX`.** Bubble Tea sends a `tea.KeyboardEnhancementsMsg` when the terminal confirms support. Use that to choose the hint text: show `shift+enter newline` when supported, otherwise `ctrl+j newline`. The hint is then always accurate, including inside tmux. If the terminal never answers, keep the legacy hint.
3. **Don't make the binding configurable to work around this.** Some apps offer an "Enter inserts newline, Ctrl+S sends" mode for people who write long messages. That's a reasonable preference to add later, but it doesn't fix the protocol problem.

### Sketch

```go
ta := textarea.New()
ta.KeyMap.InsertNewline = key.NewBinding(
    key.WithKeys("shift+enter", "ctrl+j", "alt+enter"),
)

var keys = struct{ Send key.Binding }{
    Send: key.NewBinding(key.WithKeys("enter")),
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyboardEnhancementsMsg:
        m.shiftEnterWorks = msg.SupportsKeyDisambiguation()
        return m, nil
    case tea.KeyPressMsg:
        if key.Matches(msg, keys.Send) {
            v := m.input.Value()
            if strings.HasSuffix(v, `\`) { // backslash continuation
                m.input.SetValue(strings.TrimSuffix(v, `\`))
                m.input.InsertString("\n")
                return m, nil
            }
            return m.send()
        }
    }
    var cmd tea.Cmd
    m.input, cmd = m.input.Update(msg)
    return m, cmd
}

func (m model) newlineHint() string {
    if m.shiftEnterWorks {
        return "shift+enter newline"
    }
    return "ctrl+j newline"
}
```

I wrote this from Bubble Tea v2's API, but the skill's Go reference doesn't list the exact names, so check `KeyboardEnhancementsMsg.SupportsKeyDisambiguation()` against your v2.x version before relying on it.

## Tests

Do most of the testing in unit tests on `Update`; no terminal is needed:

- `tea.KeyPressMsg{Code: tea.KeyEnter}` sends the message.
- `{Code: tea.KeyEnter, Mod: tea.ModShift}`, `{Code: 'j', Mod: tea.ModCtrl}` and `{Code: tea.KeyEnter, Mod: tea.ModAlt}` each insert a newline and don't send.
- A value ending in `\` followed by Enter inserts a newline.
- A pasted message containing newlines doesn't send.
- The hint shows the Shift+Enter text only after `KeyboardEnhancementsMsg` arrives.

Then check by hand once in each environment: kitty, tmux with default settings, and iTerm2 or Terminal.app. In the last two, Shift+Enter should still send, and the hint should say Ctrl+J.
