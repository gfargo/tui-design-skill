Mostly no. It used to be true for Ctrl+S, but it doesn't apply to a Bubble Tea app once it's running.

## Why people say it

In the terminal's default "cooked" mode, the kernel's tty driver handles some control keys before your program sees them:

- **Ctrl+S / Ctrl+Q** are flow control (XON/XOFF, the `IXON` flag). Ctrl+S freezes output, which is why people think their terminal "hung."
- **Ctrl+C** gets turned into a `SIGINT` signal (the `ISIG` flag) instead of being passed through as a keypress.

That's what a plain shell script or a line-reading CLI experiences.

## Why it doesn't apply to your app

When a Bubble Tea program starts, it puts the terminal into **raw mode**. That clears `IXON`, `ISIG`, `ICANON` and the related flags. Both keys then arrive as ordinary bytes (`0x13` for Ctrl+S, `0x03` for Ctrl+C), and Bubble Tea turns them into key messages:

```go
case tea.KeyMsg:
    switch msg.String() {
    case "ctrl+s":
        return m, m.save()
    case "ctrl+c":
        return m, m.copySelection()
    }
```

Ctrl+C doesn't quit a Bubble Tea app by itself. It only quits because most examples map `"ctrl+c"` to `tea.Quit`, and you can map it to something else.

## Real caveats

1. **The terminal emulator can grab keys before the tty sees them.**
   - Windows Terminal copies on Ctrl+C when text is selected, and some setups bind Ctrl+Shift+C/V.
   - VS Code's integrated terminal can capture keybindings unless they're passed through (`terminal.integrated.commandsToSkipShell`, `sendKeybindingsToShell`).
   - On macOS, Cmd+C and Cmd+S belong to the terminal app, but Ctrl+C and Ctrl+S are passed through.
   - tmux and screen only take their own prefix keys, so these two are fine there.
2. **Ctrl+C as "copy" goes against what users expect.** Terminal users expect Ctrl+C to interrupt or quit. If you rebind it, give them an obvious way out (`q`, `esc`, or Ctrl+Q) and show it in your help bar. Otherwise people will feel trapped.
3. **Copying to the system clipboard is separate work.** Catching the key is easy. Actually putting text on the clipboard needs either **OSC 52** (an escape sequence the terminal handles, which also works over SSH, but some terminals and tmux configs need it enabled) or a clipboard library such as `atotto/clipboard`, which only works locally.
4. **Mouse capture blocks native selection.** If you enable mouse support, users have to Shift-drag (Option-drag in iTerm2) to select text with the terminal's own selection. That's another reason an in-app copy command can be useful.
5. **Before raw mode is on, the old rules apply.** If someone presses Ctrl+S before your program starts, or after it exits, normal flow control applies. This doesn't affect your key handling.

In short: bind both keys. Ctrl+S is safe. Ctrl+C works too, as long as you leave users a clear way to quit and handle the clipboard yourself, ideally with OSC 52.
