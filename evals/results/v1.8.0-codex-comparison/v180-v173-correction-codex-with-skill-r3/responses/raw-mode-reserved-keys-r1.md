No—**both keys normally reach a Bubble Tea app in raw mode.** The claim confuses ordinary terminal input handling with raw-mode input.

| Key | Normal terminal mode | Bubble Tea raw mode |
|---|---|---|
| Ctrl+S | With XON/XOFF enabled, pauses output; Ctrl+Q resumes it | Arrives as a keypress because flow control is disabled |
| Ctrl+C | With signal processing enabled, generates SIGINT | Arrives as a keypress because terminal-generated signals are disabled |

Bubble Tea manages raw mode. The alternate screen used for full-screen display is a separate feature.

**Use Ctrl+S for save. Keep Ctrl+C for cancel or quit**, and choose another copy binding—such as `y` outside text entry—shown in your help. Ctrl+C can technically copy, but it breaks a strong terminal convention.

In Bubble Tea v2, handle `tea.KeyPressMsg` and match `msg.String()` against `"ctrl+s"` or `"ctrl+c"`; v1 uses `tea.KeyMsg`. A Ctrl+C branch returning `tea.Quit` is your app choosing to quit.

There are exceptions: terminal shortcuts or multiplexer bindings can intercept keys before Bubble Tea sees them. Zellij’s default bindings, for example, capture Ctrl+S. Provide a discoverable alternative for save and copy.