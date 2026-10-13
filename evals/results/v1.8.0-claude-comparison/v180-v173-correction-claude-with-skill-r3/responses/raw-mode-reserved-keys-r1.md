Mostly no. It was true for ordinary shell programs, but not for a full-screen Bubble Tea app.

**Why the claim is wrong for your app.** In normal "cooked" mode, the terminal driver intercepts Ctrl+C (sends an interrupt signal that usually kills the program) and Ctrl+S/Ctrl+Q (pause and resume output). Bubble Tea switches the terminal to raw mode, which turns both of those off. In raw mode:

- **Ctrl+S** reaches your app as a normal keypress, and the screen doesn't freeze. Real terminal apps bind it: nano and micro save on Ctrl+S, and helix uses it for another command. You don't need the `stty -ixon` workaround; that only helps programs that aren't in raw mode.
- **Ctrl+C** also arrives as a normal `tea.KeyPressMsg`, not as a signal. That's why the standard Bubble Tea pattern is `case "ctrl+c": return m, tea.Quit`. Ctrl+C only quits your app because your code tells it to.

**Where the claim is partly true:**

1. **Terminal emulator shortcuts.** The terminal window can take a key before raw mode matters. For example, Windows Terminal copies on Ctrl+C when text is selected. This is also why most Linux and macOS terminals use Ctrl+Shift+C or Cmd+C for copy.
2. **Multiplexers.** GNU screen with `flow on` swallows Ctrl+S and Ctrl+Q. Its default setting passes them through to raw-mode apps. tmux and screen prefix keys (Ctrl+B, Ctrl+A) never reach your app.
3. **Ctrl+Shift+C usually looks the same as Ctrl+C** unless the terminal supports an enhanced keyboard protocol like kitty's, so you can't count on telling them apart.

**What I'd do:**

- **Ctrl+S for save:** go ahead and bind it.
- **Ctrl+C for copy:** I'd avoid it. Users expect Ctrl+C to cancel or quit, and if you take that over, they can't easily get out of your app. If you bind it to copy anyway, show a clear way to exit. A better fit is `y` (the vim-style "yank") or `c` in non-text-entry contexts, sending the text to the system clipboard with OSC 52 (`tea.SetClipboard` in Bubble Tea v2). That copies through the terminal, so it also works over SSH, provided the terminal allows OSC 52 clipboard writes.
- **Mouse capture:** if you turn it on, native text selection stops working in most terminals. Users can usually still select by holding Shift while dragging, so mention that in your help text.
