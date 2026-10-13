**Give the sidebar a normal-mode shortcut, and keep Esc with a fast alternative such as Ctrl+[.** tmux sits between the terminal and your app, so it can consume or delay keys before your input handler sees them.

Two things are happening:

- **Ctrl+B is tmux’s default prefix.** tmux consumes it and waits for a tmux command; your sidebar handler receives nothing. With default bindings, pressing **Ctrl+B twice** sends one literal Ctrl+B to the app. Custom prefixes and bindings can change this.
- **Esc is ambiguous in legacy terminal input.** A lone Esc sends byte `0x1b`, but Alt combinations and many special-key sequences also begin with that byte. tmux waits briefly to distinguish them. Its `escape-time` default was **500 ms before tmux 3.5**, and is **10 ms since 3.5**. Your app’s input decoder may add another timeout.

Design around this as follows:

1. **Make `b` in normal mode toggle the sidebar**, assuming it is available. Preserve literal `b` during insert mode. Keep Ctrl+B as an optional alias, allow remapping, and expose “Toggle sidebar” through your command menu or palette if you have one. Ctrl+A is also a poor sole fallback: GNU Screen uses it, and many users rebind tmux to it.
2. **Keep Esc for leaving insert mode and add Ctrl+[.** In legacy encoding, Ctrl+[ sends the same byte as Esc, so it provides ergonomic convenience but **does not bypass the timeout**. For a genuinely distinct fast alternative, offer a configurable key such as **Ctrl+G**, after checking your keymap.
3. **Show the current mode and effective bindings.** For example: `INSERT · Esc / Ctrl+G normal` and `NORMAL · b sidebar · ? help`. Generate hints from the actual keymap.
4. **Use enhanced keyboard protocols when negotiated successfully**, while retaining legacy bindings. Support in the outer terminal alone does not establish support through tmux.

Document this optional user setting in `~/.tmux.conf`:

```tmux
set -s escape-time 10
```

A value of `0` minimizes waiting but can misdecode sequences when bytes arrive separately, especially over remote connections. Inspect the effective setting with `tmux show-options -s escape-time`; if Esc remains slow at 10 ms, investigate the app decoder’s timeout too.

Verify bare Esc, Alt combinations, arrows, and both sidebar paths inside and outside tmux, including over SSH.

For the sidebar layout, preserve the main content at **80×24**; in a **60-column split**, make the sidebar a temporary single-pane view and restore focus when it closes. Below your measured usable minimum, show a clear “terminal too small” state. Keep hints in one compact line, avoid nested borders and repeated sidebar labels, and truncate labels before content. Actual clutter counts require a rendered screen.