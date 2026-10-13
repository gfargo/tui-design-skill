There's no code in the working directory, so this is based on how terminals and Bubble Tea v2 behave, not on your implementation.

## Why it happens

**Most terminals send the same byte for Enter and Shift+Enter.** With the legacy keyboard encoding, both keys send `\r` (0x0D). There's no shift bit in that byte, so the app has nothing to tell them apart. Bubble Tea isn't dropping anything; the information never reaches it.

**Kitty works because of the kitty keyboard protocol.** At startup, Bubble Tea v2 asks the terminal for keyboard enhancements (the "disambiguate" flag). Terminals that support it (kitty, Ghostty, WezTerm, foot, recent iTerm2 and Alacritty) then send Shift+Enter as an escape sequence, e.g. `CSI 13;2u`. That sequence decodes to `shift+enter`. Terminals that don't support it ignore the request and keep sending `\r`. This includes Terminal.app, older VTE/GNOME Terminal and many embedded IDE terminals.

**tmux sits in the middle and re-encodes keys.** It parses the outer terminal's input and generates new input for the pane. By default it doesn't pass the kitty protocol through, so modifiers on Enter are lost even when the outer terminal is kitty. tmux has its own extended-keys support, but it's off by default:

```tmux
# ~/.tmux.conf  (tmux ≥ 3.2; csi-u format needs ≥ 3.5)
set -s extended-keys on            # or 'always'
set -s extended-keys-format csi-u
set -as terminal-features 'xterm*:extkeys'
```

Both the outer terminal and tmux need to support this, so you can't rely on users having it set up.

## Design

Treat Shift+Enter as a nice extra when it's available, and always provide a newline key that works without it.

1. **Accept several newline keys:**
   - `shift+enter`: works where the kitty protocol or tmux extended-keys is available.
   - `alt+enter`: sends `ESC \r`, which works in nearly every terminal and in tmux. On macOS the user may need "Option as Meta" turned on.
   - `ctrl+j`: sends LF (`\n`), which is different from CR in every terminal. This is the most reliable fallback.
   - Optional: a trailing `\` followed by Enter inserts a newline. This needs no terminal support at all (Claude Code does this).

2. **Detect support and update the help text.** Bubble Tea sends `tea.KeyboardEnhancementsMsg` when the terminal acknowledges the request. If it arrives and reports key disambiguation, advertise Shift+Enter. If it never arrives, advertise Alt+Enter / Ctrl+J. Don't show users a binding that can't work in their terminal.

3. **Handle pastes separately.** Bracketed paste arrives as `tea.PasteMsg`. Insert pasted text verbatim so that newlines inside a paste never trigger a send.

4. **Document setup** for tmux (the config above) and for terminals that let you remap Shift+Enter. For example, in VS Code or iTerm2 you can map Shift+Enter to send `\x1b\r`, which then arrives as alt+enter.

Sketch (check the exact names against the Bubble Tea v2 version you use):

```go
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyboardEnhancementsMsg:
        m.shiftEnterOK = msg.SupportsKeyDisambiguation()
        return m, nil

    case tea.PasteMsg:
        m.input.InsertString(msg.Content) // never sends
        return m, nil

    case tea.KeyPressMsg:
        switch msg.String() {
        case "shift+enter", "alt+enter", "ctrl+j":
            m.input.InsertRune('\n')
            return m, nil
        case "enter":
            if v := m.input.Value(); strings.HasSuffix(v, `\`) {
                m.input.SetValue(strings.TrimSuffix(v, `\`) + "\n")
                return m, nil
            }
            return m, m.send()
        }
    }
    var cmd tea.Cmd
    m.input, cmd = m.input.Update(msg)
    return m, cmd
}

func (m model) newlineHint() string {
    if m.shiftEnterOK {
        return "shift+enter newline"
    }
    return "alt+enter / ctrl+j newline"
}
```

If you use `bubbles/textarea`, take Enter and the newline keys out of its `KeyMap.InsertNewline` binding, or handle them before the textarea sees them. Otherwise it will insert newlines on plain Enter or swallow your keys.

In short: Enter always sends, and Shift+Enter inserts a newline only in terminals that can report it. Alt+Enter and Ctrl+J always work as fallbacks, and the help text shows whichever binding works in the current terminal.
