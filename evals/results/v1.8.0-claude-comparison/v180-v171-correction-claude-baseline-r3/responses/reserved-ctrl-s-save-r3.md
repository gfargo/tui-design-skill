**Not quite. Vim and Helix don't actually bind Ctrl+S to save:**

- **Vim** saves with `:w`. Out of the box, Ctrl+S in terminal Vim usually freezes the terminal.
- **Helix** also saves with `:w` (`:write`). In normal mode, Ctrl+S saves the current selection to the jumplist. It doesn't write the file.

Editors that do use Ctrl+S for save include micro, recent nano (which also keeps Ctrl+O), and GUI-style editors like VS Code.

**Is it safe? Yes, but only if you turn off terminal flow control.**

The hazard is XON/XOFF software flow control. When the tty has the `IXON` flag set, the kernel's terminal driver takes Ctrl+S (XOFF) before your program sees it, and it stops all output until Ctrl+Q (XON). Users then think your app has hung. That's why Vim users "freeze" their terminal with Ctrl+S.

To make it work:

1. **Clear `IXON` when you enter raw mode.** `cfmakeraw()` does this. If you set termios flags by hand, include it:
   ```c
   raw.c_iflag &= ~(IXON | ICRNL | BRKINT | INPCK | ISTRIP);
   ```
   Most TUI libraries do this for you in raw mode, including crossterm, termion, tcell, Bubble Tea, and notcurses. With ncurses, `raw()` disables it but `cbreak()` does not. Check what your library does rather than assuming.
2. **Restore the original termios on exit,** including on panic or crash, so the user's shell flow-control settings come back.
3. **Clearing `IXON` also frees Ctrl+Q,** so you can bind it (for example, to quit, like micro does).

**Remaining caveats:**

- **tmux and screen:** These normally pass Ctrl+S through once the inner app is in raw mode. Some users have custom prefix bindings that grab it, but that's their configuration, not your bug.
- **Serial consoles and some old or remote setups:** A link in between may still do its own XON/XOFF. This is rare today.
- **Expectations:** Vim and Helix users will reach for `:w`. If your editor has a command mode, supporting `:w` too costs little.
- **Make the binding configurable,** since some users have Ctrl+S mapped in their terminal emulator or window manager.

In short: Ctrl+S for save is a reasonable default as long as you disable `IXON` in raw mode and restore it on exit.
