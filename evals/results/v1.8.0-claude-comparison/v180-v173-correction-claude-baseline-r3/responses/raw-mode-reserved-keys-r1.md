**Mostly no.** In a full-screen Bubble Tea app both keys normally reach your program. Your friend is describing how the terminal behaves at a shell prompt, which isn't the mode your app runs in.

## Why the claim sounds right

At a shell prompt the terminal is in "cooked" mode, and the kernel's tty driver handles some control keys itself:

- **Ctrl+S** (byte `0x13`) is XOFF flow control (the `IXON` flag). It freezes output until you press Ctrl+Q. That's the "my terminal froze" problem.
- **Ctrl+C** (byte `0x03`) is turned into a `SIGINT` signal (the `ISIG` flag), so the program gets a signal, not a keypress.

## Why it doesn't apply to your app

When a Bubble Tea program starts, it switches the terminal to raw mode using `golang.org/x/term`'s `MakeRaw`. That turns off both `IXON` and `ISIG`. So:

- Ctrl+S arrives as a normal `tea.KeyMsg` with the string `"ctrl+s"`.
- Ctrl+C arrives as a `tea.KeyMsg` with the string `"ctrl+c"`. It is not a signal. Many Bubble Tea examples quit on Ctrl+C only because their `Update` function chooses to.

The tty settings go back to normal when your program exits.

## Where the claim can still be true

Other software between the keyboard and your app can catch keys before they arrive:

- **The terminal emulator's own shortcuts.** On macOS, copy is Cmd+C and is handled by the terminal app, so your program never sees it. Windows Terminal copies on Ctrl+C when text is selected. Some Linux terminals use Ctrl+Shift+C/V. Check the shortcut settings of the terminals your users actually use.
- **IDE terminals** (VS Code, JetBrains) can claim some Ctrl shortcuts for the editor, depending on settings.
- **Multiplexers.** tmux uses Ctrl+B by default and screen uses Ctrl+A, so those could conflict, but Ctrl+S and Ctrl+C pass through by default.

## Design concerns worth more attention

1. **Ctrl+C as copy goes against what terminal users expect.** In a terminal, Ctrl+C means "get me out of here." If it copies instead, people can feel trapped. If you keep it, make sure quitting is obvious and shown on screen (q, Esc, or Ctrl+Q). One common compromise: Ctrl+C copies when something is selected and quits or cancels otherwise. Vim-style apps usually use `y` for copy.
2. **Copying to the system clipboard is a separate problem.** Getting the key doesn't give you clipboard access. You'll need a library like `atotto/clipboard`, which doesn't work over SSH, or OSC 52 escape sequences, which work over SSH but are disabled in some terminals and in tmux unless `set-clipboard` is on.
3. **Mouse mode turns off native text selection.** If you enable mouse support, users have to hold Shift (or Option in some macOS terminals) to select text with the terminal. Mention that in your help text.

Ctrl+S for save is safe to use. Ctrl+C will also reach your app, but treat it as a design choice rather than something you have to work around.
