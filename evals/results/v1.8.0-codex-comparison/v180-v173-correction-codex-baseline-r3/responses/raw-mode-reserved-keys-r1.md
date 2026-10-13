No—that’s true in some terminal modes, but it’s not a general limitation. **Bubble Tea normally puts the terminal into raw mode**, so both keys can reach your app.

- **Ctrl+C:** In ordinary terminal mode, it sends `SIGINT`. In raw mode, Bubble Tea receives it as a key event; your `Update` method decides whether it copies, quits, or does something else.
- **Ctrl+S:** With terminal flow control enabled, it pauses output (Ctrl+Q resumes it). Raw mode normally disables that behavior, letting Bubble Tea receive Ctrl+S.

In Bubble Tea v1, you can handle them like this:

```go
case tea.KeyMsg:
    switch msg.String() {
    case "ctrl+s":
        return m, m.save()
    case "ctrl+c":
        return m, m.copy()
    }
```

A terminal emulator, multiplexer, or custom shortcut can still intercept keys before they reach your app, so test your target environments.

Also, receiving Ctrl+C and **writing to the system clipboard** are separate concerns. Clipboard support needs its own implementation, often OSC 52 for terminal apps, with support depending on the terminal and multiplexer.