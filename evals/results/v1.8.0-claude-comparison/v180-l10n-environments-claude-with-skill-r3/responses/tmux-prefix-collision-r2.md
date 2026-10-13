I've read the skill's key-handling and terminal-environment references and am writing up the answer now.

## What's happening

Both problems come from tmux, not from your app.

**Ctrl+B never reaches your app.** It is tmux's default prefix key. tmux catches it as the start of its own command and never passes it to the program in the pane. So in tmux your sidebar toggle can't be pressed. Zellij also captures Ctrl+B in its default mode, and GNU screen does the same with Ctrl+A.

**Esc is slow because tmux holds it back.** In the traditional key encoding, Esc is the same byte that starts Alt+key combos and arrow-key sequences. When tmux sees a lone Esc, it waits `escape-time` to see if more bytes follow before passing it on. That wait is **500 ms in tmux versions before 3.5** and 10 ms from 3.5 on. Users on older tmux, or with an old `tmux.conf` value, get half a second of lag on every switch out of insert mode. Your app can't make that faster, because tmux hasn't sent the key yet. If your input library adds its own wait for Esc, the two delays add up, so check that as well.

The kitty keyboard protocol solves this by giving Esc its own unambiguous code. But tmux's `extended-keys` option is off by default, so inside tmux you almost always get the old encoding. Treat the protocol as a bonus, not the fix.

## How to design around it

**1. Give every action a binding that works in the old encoding and isn't a multiplexer key.** Keep Ctrl+B as an alias for users outside tmux, but add a main binding that needs no Ctrl or Alt:
- In normal mode, use a plain key such as `\`, or a leader sequence such as `Space` `b`, for the sidebar. Bind plain keys only in normal mode so they don't interfere with typing in insert mode.
- Add "Toggle sidebar" to the command palette and the `?` help screen, if you have them.
- Let users change bindings in config. Check at startup that every action still has at least one usable binding.

**2. If `$TMUX` (or `$ZELLIJ`/`$STY`) is set, show the binding that works.** The footer and help should show `\ sidebar`, not a Ctrl+B hint the user can't press. Tell tmux users they can also press Ctrl+B twice: tmux's default `send-prefix` binding passes the second one through.

**3. Make Esc reliable without promising instant response.**
- Switch modes as soon as Esc arrives. Your app shouldn't add a delay of its own.
- Make the switch obvious: a mode label in the status bar plus a cursor shape change (block in normal, bar in insert). Reset the cursor shape on exit. That way users can see the switch happened.
- Detect the problem and say so. If `$TMUX` is set, run `tmux show -sv escape-time` once, off the UI thread. If it's high, show a one-time notice or a line in a `doctor`/health command, like Neovim's `:checkhealth` warning about the same setting.
- An optional two-key exit such as `jk` is fine as an opt-in setting. It shouldn't be the default, because it stops users from typing "jk" and needs its own timeout. `Ctrl+[` doesn't help: it sends the same byte as Esc and gets the same delay.

**4. Document the `tmux.conf` lines:**

```tmux
set -sg escape-time 10      # fixes Esc lag (already the default in tmux 3.5+)
set -g extended-keys on     # optional: newer key encoding, if the outer terminal supports it
```

## While you're touching the sidebar

tmux users often work in split panes. At 60 columns or narrower, the sidebar should collapse on its own so the main pane gets the space, with the same toggle bringing it back as an overlay. At 80×24 it can be open by default. Below your minimum size, show a clear "terminal too small" message rather than a broken layout.

## Tests

- **Keymap unit test:** every action has at least one binding that isn't Ctrl+A, Ctrl+B, or Esc-only. Run it against user configs too.
- **Footer hints:** with a synthetic `$TMUX` set, the hints show the alternate binding.
- **Mode switch:** the state test confirms Esc leaves insert mode on the first event, with no internal timer.
- **Real terminal:** one smoke test inside tmux checks that the alternate sidebar key works and the cursor shape resets on exit.
