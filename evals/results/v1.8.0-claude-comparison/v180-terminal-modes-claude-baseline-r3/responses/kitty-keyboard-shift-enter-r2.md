There's no Go code in this directory, so this answer is about how terminals behave in general, not your specific code.

## Why it happens

**In the standard terminal encoding, Shift+Enter and Enter send the same bytes.** Both send a carriage return (`\r`, 0x0D). The Shift modifier is dropped before your program gets the input. Bubble Tea isn't misreading anything: it receives a plain `enter`, so the message sends.

Kitty works because it supports the **kitty keyboard protocol**. Bubble Tea v2 asks for it at startup, and kitty then reports Shift+Enter as its own sequence (`CSI 13;2u`). Other terminals fall into three groups:

| Environment | What happens |
|---|---|
| kitty, Ghostty, WezTerm, foot, Alacritty, recent iTerm2 | Support the protocol, so Shift+Enter works. Some need it enabled (e.g. iTerm2's "Report keys using CSI u", WezTerm's `enable_kitty_keyboard`). |
| macOS Terminal.app, many older terminals | No support for extended keys. Shift+Enter is always just `\r`. |
| **tmux** | tmux is a terminal in between your app and the real one. It parses the outer terminal's input and re-encodes it for your app. It doesn't pass the kitty protocol through. It can forward modified keys using xterm's `modifyOtherKeys`/CSI-u format, but only when configured to. Even inside kitty, tmux strips the Shift by default. |

To get it working in tmux (3.2+, better on 3.5+):

```tmux
set -s extended-keys on            # or 'always'
set -as terminal-features 'xterm*:extkeys'
set -s extended-keys-format csi-u  # tmux 3.5+
```

The outer terminal still has to support extended keys, and in practice this setup doesn't work reliably everywhere. Treat it as something to put in your docs, not a fix.

## Design

**Treat Shift+Enter as a nice extra, not the only way to insert a newline.** Specifically:

1. **Enter always sends. Provide several ways to insert a newline, including some that work everywhere:**
   - `shift+enter` works when the terminal supports it.
   - `ctrl+j` sends LF (`\n`), which differs from Enter's CR even in the standard encoding. It works in every terminal and in tmux.
   - `alt+enter` arrives as ESC + `\r`, which is also distinguishable. On macOS it needs "Option as Meta" turned on.
   - Optionally, a `\` at the end of the line followed by Enter could insert a newline instead of sending. It needs no special keys at all.

2. **Detect support and change the hint text.** Bubble Tea v2 sends a `tea.KeyboardEnhancementsMsg` once it knows what the terminal supports. Show "shift+enter: newline" only when that's true, and "ctrl+j: newline" otherwise. That way users never see a key hint that does nothing.

3. **Handle pastes separately.** Rely on bracketed paste (`tea.PasteMsg`) so newlines in pasted text are inserted into the message, never treated as Enter.

4. **Optional:** add a setting that swaps the keys (Enter = newline, Ctrl+S or similar = send) for people who mostly write multi-line messages.

Sketch (exact v2 names may differ slightly by version):

```go
type model struct {
    ta            textarea.Model
    shiftEnterOK  bool
}

func newModel() model {
    ta := textarea.New()
    // Default InsertNewline includes "enter" — take it out so Enter can send.
    ta.KeyMap.InsertNewline = key.NewBinding(
        key.WithKeys("shift+enter", "ctrl+j", "alt+enter"),
    )
    return model{ta: ta}
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyboardEnhancementsMsg:
        m.shiftEnterOK = msg.SupportsKeyDisambiguation()
    case tea.KeyPressMsg:
        if msg.String() == "enter" {
            if v := m.ta.Value(); strings.HasSuffix(v, "\\") { // continuation
                m.ta.SetValue(strings.TrimSuffix(v, "\\") + "\n")
                return m, nil
            }
            return m.send()
        }
    }
    var cmd tea.Cmd
    m.ta, cmd = m.ta.Update(msg)
    return m, cmd
}

func (m model) newlineHint() string {
    if m.shiftEnterOK {
        return "shift+enter newline"
    }
    return "ctrl+j newline"
}
```

Two things to watch for:
- **Remove `enter` from the textarea's `InsertNewline` binding.** Otherwise the textarea adds a newline as well as your app sending the message.
- **Don't bind send to `ctrl+m`.** It's the same byte as Enter in the standard encoding.

In short, Shift+Enter needs terminal support that many terminals and tmux don't provide by default. Keep it, but make sure `ctrl+j` (and ideally `alt+enter` or `\`+Enter) always works, and show the hint that matches what the terminal supports.
