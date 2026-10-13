## What's happening

Both problems come from tmux, not from your app logic.

**Ctrl+B does nothing because tmux takes it.** Ctrl+B is tmux's default prefix key. tmux uses it to start its own commands and never passes it to the program in the pane, so your app never receives it. Other multiplexers block other keys in the same way. GNU screen takes Ctrl+A. Zellij's default mode takes Ctrl+G/P/T/N/H/S/O/Q/B and many Alt keys.

**Esc lags because the Esc byte is ambiguous.** A lone Esc is the same byte (`0x1b`) that starts arrow keys, function keys, and Alt+key sequences. When tmux sees it, it waits `escape-time` to find out whether more bytes are coming. The default wait was **500 ms before tmux 3.5** and is 10 ms since then. Users on older tmux therefore feel half a second of lag on every Esc. Your input layer may add its own wait on top. For example, ncurses' `ESCDELAY` defaults to 1000 ms, and many frameworks have a similar timeout.

## How to design around it

**1. Give every action a path that doesn't use a multiplexer key.**
- Make the main sidebar toggle a plain key in normal mode, such as `b`, `\`, or a leader sequence like `Space e` with a which-key popup. Normal mode is where users switch layouts anyway.
- Keep Ctrl+B as a secondary binding. It still works outside tmux, and inside tmux users can press `Ctrl+B Ctrl+B`, since tmux's default config passes a second prefix through.
- Add a command palette entry ("Toggle sidebar"). If the sidebar header is clickable, a mouse click can be another shortcut.
- Let users rebind keys, because some users have changed their prefix to Ctrl+A, Ctrl+Space, and so on.
- Add a keymap test: no action may have only keys from {Ctrl+B, Ctrl+A, Zellij's Ctrl set, Alt+*}.

**2. Make the help match the terminal.** If `$TMUX` is set, don't list Ctrl+B in the footer or `?` help. Show the binding that will actually work. Build the footer and help from one keymap so they can't drift apart.

**3. Reduce the Esc delay in your app, and help users fix tmux.**
- Set your own input layer's Esc timeout to roughly 25–50 ms instead of a library default like 1000 ms. Very low values can split real escape sequences over slow SSH, so make it configurable.
- Your app can't change tmux's delay, but it can detect the problem. When `$TMUX` is set, run `tmux show-options -sv escape-time`. If the value is over about 50, show a one-time hint or a line in a `doctor`/health command, like Neovim's `:checkhealth`. Document the fix:
  ```tmux
  set -sg escape-time 10
  ```
- Where the terminal supports the Kitty keyboard protocol ("disambiguate" flag), use it. Esc then arrives as its own code, so no guessing is needed. Inside tmux, though, you usually get the old encoding unless the user turns on `extended-keys`. Treat the protocol as a bonus, not the fix.
- Offer a second way out of insert mode. Note that `Ctrl+[` doesn't help: it sends the same Esc byte. Ctrl+C is a reasonable choice, since leaving insert mode counts as cancelling and Vim does the same. Users who want a `jk`-style chord can set one up.

**4. Make mode changes visible immediately.** Change the cursor shape (bar in insert, block in normal), update a `NOR`/`INS` label in the status line, and reset the cursor shape on exit. Users can then tell whether the delay is in the input or whether they just couldn't see the change. Weak mode indicators make any lag feel worse.

## Testing

- Unit-test the keymap: every action has a non-Ctrl, non-Alt binding, and the help text matches the bindings.
- Unit-test the Esc handling with fake input: a lone Esc becomes "exit insert" within your timeout, and a full sequence (`ESC [ A`) becomes an arrow key, not Esc plus `[A`.
- Run one smoke test in a real terminal inside tmux, with both the old 500 ms and the new 10 ms `escape-time`, to confirm the sidebar toggle and leaving insert mode behave as expected.

If you tell me the framework (Bubble Tea, Ratatui/crossterm, Textual, Ink, …), I can point to the exact setting for its Esc timeout and how to turn on the Kitty keyboard protocol.
