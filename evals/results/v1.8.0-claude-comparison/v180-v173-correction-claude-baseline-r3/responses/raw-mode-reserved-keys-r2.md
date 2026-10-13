**Mostly no.** Both keys reach a Bubble Tea app, because Bubble Tea puts the terminal in raw mode. The claim is true only for programs running in the terminal's default cooked mode.

**Why the myth exists**

In cooked mode, the kernel's tty driver handles these keys before your program sees them:
- **Ctrl+S / Ctrl+Q** are XON/XOFF flow control (the `IXON` flag). Ctrl+S freezes output, which is why people think the terminal "ate" it.
- **Ctrl+C** sends `SIGINT` (the `ISIG` flag) instead of arriving as input.

Raw mode turns off `IXON` and `ISIG`, so both keys arrive as ordinary bytes (`0x13` and `0x03`). Bubble Tea turns them into key messages:

```go
case tea.KeyMsg:
    switch msg.String() {
    case "ctrl+s":
        return m, m.save()
    case "ctrl+c":
        return m, m.copySelection()
    }
```

This also works over SSH and inside tmux. On Windows, Bubble Tea sets the console mode so Ctrl+C arrives as a key there too.

**Real caveats**

1. **Ctrl+C no longer quits.** Most Bubble Tea examples map `ctrl+c` to `tea.Quit`. If you use it for copy, you need a clearly shown quit key (`q`, `ctrl+q`, or `esc`). Users instinctively press Ctrl+C to escape a stuck app, so think about what happens when nothing is selected. A common pattern is to copy if there's a selection and quit (or ask to confirm quitting) if there isn't.
2. **Some terminal emulators bind these keys themselves**, before your app sees them:
   - Windows Terminal can copy on Ctrl+C when text is selected with the mouse.
   - VS Code's integrated terminal can send some shortcuts to the editor instead of the shell (see `terminal.integrated.commandsToSkipShell`).
   - Some users have custom keybindings in their terminal.

   These are per-environment exceptions, not the general rule.
3. **Copying from a terminal app doesn't automatically use the system clipboard.** Use OSC 52 (Bubble Tea v2 has `tea.SetClipboard`; in v1 you can write the escape sequence yourself) or a library like `atotto/clipboard`. OSC 52 also works over SSH, but some terminals and tmux setups need it enabled (`set -g set-clipboard on`).
4. **Raw mode only applies while the program is running.** If you hand the terminal to a subprocess (`tea.ExecProcess`), the normal Ctrl+C/Ctrl+S behavior applies inside that subprocess.

On macOS, Cmd+C/Cmd+V belong to the terminal app and never reach you. Ctrl+C and Ctrl+S do reach you, so there's no conflict there.

So go ahead and bind them. Just make sure there's still an obvious way to quit and that copying actually puts the text on the system clipboard.
