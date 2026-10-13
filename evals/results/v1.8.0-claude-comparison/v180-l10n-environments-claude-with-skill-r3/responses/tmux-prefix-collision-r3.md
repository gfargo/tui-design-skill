## What's happening

Both problems come from tmux. It sits between the terminal and your app and reads every key first.

**Ctrl+B does nothing because tmux keeps it.** Ctrl+B is tmux's default prefix key. tmux consumes it and waits for the next key, so the keypress never reaches your app. No change inside the app can get it back. Zellij's default mode also captures Ctrl+B, and GNU screen does the same with Ctrl+A.

**Esc lags because of tmux's `escape-time`.** A lone `ESC` byte looks exactly like the start of an Alt-key or escape sequence. So tmux holds it for `escape-time` to see whether more bytes follow. Before tmux 3.5 the default was **500 ms**; since 3.5 it's 10 ms. Users with older tmux, or with a config that sets it high, feel a half-second lag on every mode switch. Your app doesn't receive the key until tmux releases it.

Two related points:
- If your input layer also waits for a follow-up byte after `ESC`, that wait is added on top of tmux's.
- The kitty keyboard protocol sends a plain Esc as its own unambiguous code, but it won't help here. Inside tmux you get the legacy encoding unless the user turns on `extended-keys`, which is off by default. And tmux's delay happens before your app sees anything.

## How to design around it

**1. Never make a Ctrl key the only way to toggle the sidebar.**
- Add a binding that works in normal mode and doesn't use Ctrl or Alt, such as `\` or a leader sequence. This also gets past Zellij.
- Keep Ctrl+B as an extra binding for users outside tmux, but don't present it as the main one.
- Put "Toggle sidebar" in the help screen and, if you have one, the command palette. Every key-bound action should also be a palette command.
- Make the keymap configurable, so users who changed their tmux prefix can choose their own binding.
- When `$TMUX` is set, show the working binding in the footer and help instead of Ctrl+B. (Use `$ZELLIJ` for Zellij and `$STY` for screen.)

**2. Make Esc instant on your side and help users fix tmux.**
- Handle a lone `ESC` right away, or with a very short timeout. Don't add your own long disambiguation delay.
- Detect tmux and check the setting with `tmux show -sv escape-time`. If it's above about 20 ms, show a one-time, dismissible hint, similar to Neovim's `:checkhealth`. Also list it in a `doctor`/`--check` command if you have one.
- Document the config line:
  ```tmux
  set -sg escape-time 10
  ```
  Avoid recommending `0`. Over a slow SSH link, Alt-key sequences can then arrive split and be read as Esc followed by a letter.
- Optionally, offer a configurable two-key insert-mode escape like `jk`, off by default. It costs some typing latency and can collide with real text, so users should opt in.
- Change the mode indicator and cursor shape (bar in insert, block in normal) the moment the key arrives. Users can then tell whether the lag comes from tmux or from your app.

**3. Document what your app needs from tmux.** Add a short "Running inside tmux" section with `escape-time`, plus any other options you rely on: `focus-events on` if you use focus reports, `extended-keys` if you offer kitty-protocol bindings as shortcuts, and `set-clipboard on` for OSC 52.

**4. Test it.** Write unit tests that feed a lone `ESC` event into the update logic and check the mode changes immediately. Then run one end-to-end smoke test inside a real tmux session with default settings to confirm the sidebar toggle and mode switch work there.

If you tell me which framework you use (Bubble Tea, Ratatui/crossterm, Textual, Ink), I can point you to its exact Esc-timeout setting and keymap API.
