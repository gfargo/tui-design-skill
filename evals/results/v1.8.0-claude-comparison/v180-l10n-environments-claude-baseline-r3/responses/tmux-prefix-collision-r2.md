The working directory is empty, so I couldn't check your key handling code. This answer covers how tmux and terminals behave in general. Both problems come from tmux sitting between the terminal and your app.

## 1. Ctrl+B does nothing: tmux uses it first

**Ctrl+B is tmux's default prefix key.** tmux reads it as "the next key is a tmux command" and never passes it to your app. Your handler isn't broken; it never receives the key. Users who set their prefix to Ctrl+A (common for GNU screen users) will have the same problem with any Ctrl+A binding you add.

Other keys that often get taken before they reach a TUI:

| Key | Usually taken by |
|---|---|
| `Ctrl+B`, `Ctrl+A` | tmux / screen prefix |
| `Ctrl+S`, `Ctrl+Q` | XON/XOFF flow control (freezes and unfreezes output) unless `ixon` is off |
| `Ctrl+Z`, `Ctrl+C`, `Ctrl+\` | Job control and signals (SIGTSTP, SIGINT, SIGQUIT) |
| `Ctrl+H` | Same byte as Backspace in many terminals |
| `Ctrl+I`, `Ctrl+M`, `Ctrl+[` | Same bytes as Tab, Enter and Esc |
| `Ctrl+Shift+*`, `Ctrl+;`, `Ctrl+1` | Not representable in legacy terminal encoding at all |
| `Cmd+*` (macOS), `Ctrl+Shift+T/N/W` | The terminal emulator itself |

## 2. Esc feels laggy: tmux's `escape-time`

The terminal sends **Esc as the single byte `0x1b`.** That same byte also starts every escape sequence: arrow keys (`\e[A`), function keys, and Alt+key (`\e` followed by the key). When a program sees a lone `0x1b`, it can't tell yet whether the user pressed Esc or a sequence is still arriving. So it waits briefly to see if more bytes follow.

- **tmux waits too.** Its `escape-time` setting defaults to **500 ms** in older versions. Newer releases lowered it to 10 ms, but many distros and long-lived configs still have the old value. tmux holds the Esc for that long before passing it on.
- **Your own input library may add another wait.** ncurses uses `ESCDELAY`, default 1000 ms. Other libraries have similar timeouts. The delays stack: tmux's wait, then yours.

Half a second on the key users press most often in a modal UI feels very laggy.

## How to design around it

### Key bindings
1. **Don't put core actions on known-taken keys.** Move the sidebar toggle off Ctrl+B. Good options:
   - A leader-key sequence such as `Space e` or `\ b` in normal mode. tmux never takes these, and they fit a modal UI.
   - An F-key, or a plain letter in normal mode.
   - Ctrl+letter keys that are rarely claimed, such as `Ctrl+E`, `Ctrl+O` or `Ctrl+G`. Even these can clash with readline habits, so test them.
2. **Make every binding remappable** through a config file. Someone's terminal or multiplexer will always take a key you didn't expect.
3. **Give every action a second route**, such as a command palette (`:` or `Ctrl+P`) or a menu. Then a stolen key costs a shortcut, not the feature.
4. **Avoid combinations legacy terminals can't encode.** Use Ctrl+Shift or Ctrl+punctuation only as optional extras when an enhanced keyboard protocol is active (see below).

### Esc latency
1. **Set your own escape timeout low**, about 10–50 ms (e.g. `ESCDELAY=25`, or your library's equivalent). Modern links deliver a whole sequence in one read, so a long wait buys nothing.
2. **Read input in chunks and parse greedily.** If one `read()` returns `\e[A`, it's an arrow key. If it returns just `\e` and nothing arrives within the short timeout, it's Esc. Never parse one byte at a time on a slow timer.
3. **Use the kitty keyboard protocol when available** (`CSI > 1 u`). Under it, Esc arrives as an unambiguous sequence, with no timeout needed, and modifiers like Ctrl+Shift become usable. kitty, WezTerm, foot, Ghostty and recent iTerm2 support it. tmux passes it through only in recent versions with `extended-keys` turned on, so detect support and fall back cleanly.
4. **Offer an Esc alternative** for leaving insert mode. `Ctrl+[` sends the same byte, so it doesn't avoid the delay. A configurable chord like `jk` or `Ctrl+C` does.
5. **Tell users about tmux's setting.** Your app can't fix tmux's delay, so put this in your docs or troubleshooting page:
   ```tmux
   # ~/.tmux.conf
   set -sg escape-time 10
   ```
   Your app can also detect `$TMUX`, query the value with `tmux show -sv escape-time`, and show a one-time hint if it's high.

### A quick check for both
Add a "key debug" mode, either a hidden command or a `--keytest` flag, that shows the raw bytes and the decoded key for each press. Users can then see right away whether a key reaches your app at all, and how long Esc takes to arrive.

**Short version:** move the sidebar off Ctrl+B to a leader-key sequence, keep everything remappable, set a short escape timeout of about 25 ms, use the kitty keyboard protocol when it's available, and document `escape-time` for tmux users.
