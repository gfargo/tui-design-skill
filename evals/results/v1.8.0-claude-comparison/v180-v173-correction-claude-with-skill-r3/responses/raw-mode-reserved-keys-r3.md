No, that's mostly wrong for a full-screen Bubble Tea app. It's half-true for plain line-mode programs, which is probably where the advice came from.

**Why it's mostly wrong**

In cooked (line) mode, the terminal driver handles these keys itself. Ctrl+C sends SIGINT, and Ctrl+S/Ctrl+Q are XON/XOFF flow control: Ctrl+S freezes output. Bubble Tea switches the terminal to raw mode, though, and raw mode turns that handling off. It clears `ISIG` and `IXON`, the same as `cfmakeraw`. So:

- **Ctrl+S** reaches your app as an ordinary `tea.KeyPressMsg` with the string `"ctrl+s"`. It won't freeze the screen, and you don't need `stty -ixon`. nano and micro save on Ctrl+S, and helix binds it too.
- **Ctrl+C** also reaches you as a `"ctrl+c"` keypress, not as SIGINT. The process only stops if your `Update` returns `tea.Quit` or `tea.Interrupt`.

**The catch with Ctrl+C**

You *can* bind it, but users expect Ctrl+C to cancel or quit. If you make it "copy", a user trying to exit gets nothing, or a copy. If you take it anyway, give people an obvious exit and show it in your help bar. A common compromise:

- Ctrl+C copies when something is selected, and otherwise cancels or quits.
- Or use `y` for yank/copy (the TUI convention) and leave Ctrl+C as quit.

Also note: on macOS, Cmd+C is the terminal emulator's own copy shortcut and never reaches your app. Users can still copy text that way, so you may not need Ctrl+C for copy at all.

**Where keys really can get eaten**

- **GNU screen with `flow on`** swallows Ctrl+S and Ctrl+Q. The default (`auto`) passes them through to raw-mode apps.
- **Multiplexer prefixes** never reach you: tmux's Ctrl+B and screen's Ctrl+A.
- **Emulator shortcuts** that the user has bound to Ctrl+key, such as copy-on-Ctrl+Shift+C in some Linux terminals.

**For the copy itself**

Use `tea.SetClipboard`, which sends OSC 52 and works over SSH. Since some terminals turn OSC 52 off, fall back to `pbcopy`, `xclip` or `wl-copy`.

A minimal sketch:

```go
case tea.KeyPressMsg:
    switch msg.String() {
    case "ctrl+s":
        return m, m.save()
    case "ctrl+c":
        if m.hasSelection() {
            return m, tea.SetClipboard(m.selectedText())
        }
        return m, tea.Quit
    }
```

Ctrl+S for save is fine as it is. For Ctrl+C, keep quit as its fallback behavior.
