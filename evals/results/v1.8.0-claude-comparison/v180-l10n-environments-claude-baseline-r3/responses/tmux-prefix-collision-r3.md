The directory is empty, so this is based on how tmux and terminals work, not on your code. Both problems come from tmux sitting between the terminal and your app.

## 1. Ctrl+B does nothing: tmux takes it first

**Ctrl+B is tmux's default prefix key.** tmux catches it and waits for a command key (like `c` or `%`), so your app never sees it. Users can get it through by pressing **Ctrl+B Ctrl+B**, because tmux's default `send-prefix` binding passes one through. Nobody will find that on their own, though.

Other combos that are risky as default bindings:

| Key | Who takes it |
|---|---|
| Ctrl+B | tmux prefix |
| Ctrl+A | GNU screen prefix, and a very common custom tmux prefix |
| Ctrl+S / Ctrl+Q | XON/XOFF flow control (freezes output if `ixon` is on and you're not in raw mode) |
| Ctrl+Z, Ctrl+C, Ctrl+\\ | Job control and signals, unless you fully own raw mode |
| Ctrl+Space | Popular custom tmux prefix; also sends NUL, which some stacks handle badly |
| Ctrl+H / Ctrl+I / Ctrl+M / Ctrl+[ | Same bytes as Backspace, Tab, Enter and Esc in legacy encoding |

## 2. Esc feels laggy: the escape-sequence timeout

The Esc key sends the single byte `\x1b`. That same byte also starts arrow keys (`\x1b[A`), Alt+key (`\x1bx`), function keys and so on. When something reads `\x1b`, it can't tell yet whether that was Esc or the start of a longer sequence. So it **waits** to see if more bytes arrive.

- **tmux** does this wait, set by `escape-time`. The default was **500 ms** for years and only dropped to 10 ms in tmux 3.5, so many users still have half-second lag.
- **Your app probably waits too**: ncurses `ESCDELAY` defaults to 1000 ms, and many TUI libraries have their own timeout.
- The two waits **add up**. Over SSH, network jitter makes it worse.

## Design recommendations

**Keybindings**
1. **Pick a sidebar default that tmux doesn't own.** Good choices are a plain key in normal mode (vim-style apps use something like `\` or `gb`), a leader sequence (`Space e`), or an F-key. Alt+key avoids the tmux prefix, but it's sent as ESC-prefixed bytes, so it has the same ambiguity as Esc.
2. **Make every binding remappable** through a config file. Someone's prefix will always clash with something.
3. **Always offer a second route**: a command palette entry or a `:sidebar` command, so any action still works if a key gets swallowed.
4. **Check for tmux/screen** via `$TMUX` / `$STY`. You can then pick safe defaults or show a one-time hint like "Ctrl+B is your tmux prefix; sidebar is bound to X."

**Esc latency**
1. **Keep your own escape timeout short**, around 25–50 ms (`ESCDELAY=25` for ncurses, or your library's equivalent). Local terminals deliver whole sequences in one read, so a short timeout is safe.
2. **Use a better keyboard protocol when it's available.** The kitty keyboard protocol (CSI u) encodes Esc without ambiguity, so there's no wait at all. tmux supports this with `set -s extended-keys on`, and modern terminals like kitty, WezTerm, foot, Ghostty and recent iTerm2 support it too. Turn it on when the terminal supports it, and fall back to the timeout otherwise.
3. **Document the tmux setting** in a troubleshooting page and/or a startup check:
   ```tmux
   set -sg escape-time 10
   set -s extended-keys on        # optional, enables unambiguous keys
   ```
   You can read the current value with `tmux show -sv escape-time` and warn if it's over about 50.
4. **Offer another way out of insert mode** that doesn't use Esc, for example Ctrl+C or a configurable chord like `jk`. Ctrl+[ won't help because it sends the same byte as Esc.

**Summary:** don't ship Ctrl+B or Ctrl+A as defaults, make keys remappable and reachable through a command palette, keep your Esc timeout short, use CSI u when available, and tell tmux users to set `escape-time` low.
