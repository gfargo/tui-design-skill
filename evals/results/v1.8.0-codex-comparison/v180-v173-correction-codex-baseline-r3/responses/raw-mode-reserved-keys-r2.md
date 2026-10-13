No. That advice applies to conventional terminal settings, not generally to a Bubble Tea app.

By default, Bubble Tea puts terminal input into **raw mode**, so both keys normally reach your `Update` method:

```go
case tea.KeyMsg:
    switch msg.String() {
    case "ctrl+s":
        // Save.
    case "ctrl+c":
        // Copy.
    }
```

Under conventional terminal settings:

- **Ctrl+S** can pause output through software flow control (XON/XOFF).
- **Ctrl+C** generates an interrupt signal instead of arriving as a keypress.

Raw mode disables those behaviors. Running full-screen via the alternate screen buffer is separate; **raw mode is what matters here**.

A terminal emulator, OS shortcut, or intermediary can still intercept keys before your app receives them. But neither key is inherently unavailable. If you use Ctrl+C for copy, replace any existing `"ctrl+c"` → `tea.Quit` handler and provide another obvious quit shortcut.