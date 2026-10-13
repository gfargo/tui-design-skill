**Mostly no. It's true for ordinary command-line programs, but not for a full-screen Bubble Tea app.**

### Why the claim exists
In normal line mode, the terminal driver handles certain keys before your program sees them:
- **Ctrl+C** sends a SIGINT signal (interrupt).
- **Ctrl+S / Ctrl+Q** are XON/XOFF flow control. This is the old "my terminal froze" problem, usually fixed with `stty -ixon`.

### Why it doesn't apply to you
Bubble Tea switches the terminal to raw mode. Raw mode turns off signal generation and clears `IXON`, so both keys arrive as ordinary keypresses: `tea.KeyMsg` with `"ctrl+s"` and `"ctrl+c"`. No SIGINT is sent and nothing freezes. Real apps rely on this: nano and micro save on Ctrl+S, and helix binds both Ctrl+S and Ctrl+C to its own commands.

### What can actually take the keys before your app sees them
- **Zellij:** its default mode captures Ctrl+S, along with Ctrl+G/P/T/N/H/O/Q/B. Its "Unlock-First" preset frees them.
- **GNU screen with `flow on`:** this swallows Ctrl+S and Ctrl+Q. The default (`auto`) passes them through to raw-mode apps.
- **tmux:** only the prefix key (Ctrl+B by default) is taken. Ctrl+S is fine.
- **macOS:** Cmd+C is handled by the terminal emulator and never reaches any app. Users there will instinctively reach for Cmd+C, not Ctrl+C.

So always offer a second route to every action, such as a command palette or a `:w`-style command, so users of those setups can still save.

### Ctrl+S for save: go ahead
It's well established and works.

### Ctrl+C for copy: it will work, but I'd advise against it
The key does arrive. The problem is the convention: users press Ctrl+C to cancel or quit, and if your app copies instead, they feel trapped. If you take Ctrl+C anyway, give an obvious exit and show it on screen. Better options:
- Bind copy to `y` (yank) in navigation views, and keep Ctrl+C as cancel/quit.
- Or overload it the way Windows Terminal does: Ctrl+C copies when something is selected and cancels/quits when nothing is.

### Making copy actually reach the clipboard
Use OSC 52, an escape sequence that asks the terminal to set the system clipboard. Bubble Tea v2 provides it as `tea.SetClipboard`, and it works over SSH. Still, treat it as best-effort:
- Some terminals disable it.
- Under tmux it needs `set -g set-clipboard on`.
- Payloads are limited to roughly 75 KB.

When you're not over SSH, fall back to `pbcopy`, `wl-copy`, or `xclip`.

One related point: since raw mode also disables the driver's Ctrl+Z, handle suspend through the framework (`tea.Suspend`), which puts the terminal back in its normal state before stopping.
