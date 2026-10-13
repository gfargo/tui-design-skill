No Go files turned up in the working directory, so this answer is based on how terminals and Bubble Tea v2 behave, not on your code.

## Why it breaks

**Most terminals send the same byte for Enter and Shift+Enter.** In the traditional encoding, Enter sends a carriage return (`\r`, 0x0D). Shift doesn't change it, so Shift+Enter also sends `\r`. The modifier never reaches your program. Bubble Tea isn't dropping it; it was never there.

**kitty works because of an extended key protocol.** Bubble Tea v2 asks the terminal for better key reporting at startup (the kitty keyboard protocol, also called "CSI u"). Terminals that support it, such as kitty, Ghostty, WezTerm, foot and recent Alacritty, then send Shift+Enter as its own sequence (`ESC [ 13 ; 2 u`), and you get `"shift+enter"`. Terminal.app, the VS Code terminal by default, older xterm setups and many others ignore the request and keep sending `\r`.

**tmux adds a second problem.** tmux sits between the terminal and your app: it decodes the keys itself and re-encodes them for the pane. So even if the outer terminal is kitty:
- tmux won't forward extended keys unless it's configured to, and it doesn't relay the kitty protocol request. Its own support is based on xterm's `modifyOtherKeys`.
- By default, tmux turns Shift+Enter back into a plain `\r`.

You can partly fix this in tmux (3.2+, ideally 3.5+):
```tmux
set -s extended-keys on            # or 'always'
set -s extended-keys-format csi-u  # tmux 3.5+
set -as terminal-features 'xterm*:extkeys'
```
But you can't require every user to do this, and some outer terminals still won't cooperate.

## Recommended design

Treat Shift+Enter as a nice extra when it works, never the only way to get a newline.

1. **Enter always sends.** No exceptions and no guessing based on timing.
2. **Bind several newline keys, all active at once:**
   - `shift+enter`: works when the terminal supports extended keys.
   - `alt+enter`: sends `ESC \r`. This works almost everywhere, including tmux with default settings.
   - `ctrl+j`: sends a line feed (0x0A), which is a different byte from Enter's `\r` even in the old encoding. Works everywhere.
   - Optionally, a backslash followed by Enter becomes a newline. This catches users who don't know the other keys.
3. **Check what the terminal supports and adjust the help text.** Watch for `tea.KeyboardEnhancementsMsg`. If key disambiguation is supported, show "shift+enter newline". Otherwise show "alt+enter / ctrl+j newline". Don't advertise a key that can't work in the current terminal.
4. **Handle multi-line paste separately.** Make sure bracketed paste is on, so pasted text arrives as `tea.PasteMsg` and gets inserted as-is. Otherwise a pasted newline looks like Enter and sends a half-finished message.
5. **Document the setup:** the tmux snippet above, and how to make Shift+Enter send `ESC \r` in iTerm2 or VS Code (`terminal.integrated.sendKeybindingsToShell` or a custom keybinding). Claude Code's `/terminal-setup` command does this same configuration.
6. **Optional:** a setting that swaps the keys (Enter adds a newline, Ctrl+Enter or Alt+Enter sends) for people who write long messages.

## Wiring it up with the bubbles v2 textarea

The textarea's default newline binding is `enter`/`ctrl+m`, so you need to replace it and handle Enter yourself before the textarea sees it:

```go
ta := textarea.New()
ta.KeyMap.InsertNewline = key.NewBinding(
    key.WithKeys("shift+enter", "alt+enter", "ctrl+j"),
    key.WithHelp("shift+enter", "newline"),
)

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyboardEnhancementsMsg:
        m.shiftEnterOK = msg.SupportsKeyDisambiguation()
        // update help text accordingly
    case tea.KeyPressMsg:
        if msg.String() == "enter" {
            v := m.ta.Value()
            if strings.HasSuffix(v, "\\") { // backslash-Enter fallback
                m.ta.SetValue(strings.TrimSuffix(v, "\\") + "\n")
                return m, nil
            }
            return m, m.send(v)
        }
    }
    var cmd tea.Cmd
    m.ta, cmd = m.ta.Update(msg)
    return m, cmd
}
```

(Method and field names have changed a bit across v2 pre-releases, so check them against the version you're on.)

The short version: in the old encoding, Shift+Enter and Enter are the same byte, and tmux re-encodes keys in a way that hides the difference. Keep Enter for sending, accept Shift+Enter when the terminal can report it, and always give users Alt+Enter and Ctrl+J as fallbacks.
