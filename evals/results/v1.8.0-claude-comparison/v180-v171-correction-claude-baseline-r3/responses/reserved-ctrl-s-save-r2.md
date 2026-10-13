Mostly yes, but one part of the premise is wrong and there's one real pitfall.

**Neither vim nor helix binds Ctrl+S to save by default.**
- **Vim** leaves Ctrl+S unbound. People add `nnoremap <C-s> :w<CR>` themselves, and the advice that comes with it is about the problem below.
- **Helix** uses Ctrl+S for `save_selection`, which adds the current position to the jumplist. You save with `:w`.
- Editors that do save on Ctrl+S include **micro**, **nano** (newer versions, alongside ^O) and **kilo**-style editors. They're the better examples to follow.

**The pitfall is XON/XOFF flow control.** Ctrl+S sends byte 0x13 (XOFF). If the terminal's `IXON` flag is set, the kernel's tty layer handles that byte itself: output freezes until Ctrl+Q, and your app never sees the key. To users, the app looks hung. That's why the binding has a bad reputation.

It's safe if you clear `IXON` when you enter raw mode:
- `cfmakeraw()` and the usual raw-mode recipes (`tcsetattr` with `~(IXON | ICRNL | …)` on `c_iflag`) do this already.
- Most TUI libraries do it for you: crossterm's `enable_raw_mode`, termion, and ncurses `raw()`. Note that ncurses `cbreak()` alone does not. With hand-rolled termios, make sure `IXON` is cleared.
- Restore the original termios on exit, including on panic or signal.

When `IXON` is off, 0x13 reaches your app through SSH, tmux and screen too, since each layer passes it along to the inner pty.

**Smaller things to know:**
- Ctrl+Q (XON) has the same issue. Clearing `IXON` frees it too, which is handy for a quit binding.
- In legacy terminal encoding, Ctrl+S and Ctrl+Shift+S send the same byte. You can only tell them apart if you opt into the kitty keyboard protocol or `modifyOtherKeys`.
- In the rare case where `IXON` stays on (unusual tty setups or wrapper scripts), offer a fallback such as a `:w`-style command or a remappable binding, so users aren't stuck.

So binding Ctrl+S to save by default is reasonable for an editor-like TUI, as long as you explicitly disable `IXON` and don't rely on the user's `stty` settings.
