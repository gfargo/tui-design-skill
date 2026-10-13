No—that’s true of some terminal modes, but generally **not of a Bubble Tea app**.

In normal “cooked” terminal mode:

- **Ctrl+C** makes the terminal driver send `SIGINT`.
- **Ctrl+S** can pause terminal output when software flow control is enabled.

Bubble Tea puts the terminal into **raw mode**, which disables those behaviors. Both keys normally arrive as key events, so you can bind them:

```go
case tea.KeyMsg:
    switch msg.String() {
    case "ctrl+s":
        return m, saveCmd
    case "ctrl+c":
        return m, copyCmd
    }
```

Many Bubble Tea examples explicitly bind Ctrl+C to `tea.Quit`; that’s an application choice, so replace that binding and provide another way to quit.

Two caveats: a terminal emulator or multiplexer can have shortcuts that intercept keys, and receiving Ctrl+C doesn’t itself copy anything—you still need clipboard support. Full-screen mode alone doesn’t determine key handling; raw mode does.