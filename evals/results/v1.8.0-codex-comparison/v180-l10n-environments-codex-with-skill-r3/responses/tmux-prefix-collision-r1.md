**Give the sidebar a printable shortcut in normal mode, and keep Esc with an additional insert-mode exit binding.** Both symptoms arise before your app receives the key.

- **Ctrl+B is tmux’s default prefix.** tmux consumes it while waiting for a command; your sidebar handler never sees it. With the default configuration, pressing **Ctrl+B twice** sends one Ctrl+B to the app. That’s a useful workaround, but a poor primary interaction.
- **Esc is ambiguous in legacy terminal input.** A standalone Esc uses the same initial byte as many special-key and Alt sequences. tmux waits briefly to distinguish them. Its default `escape-time` was **500 ms before tmux 3.5**, and is **10 ms since 3.5**. Your input library may add another decoding timeout.

Design around this as follows:

1. **Use `b` for the sidebar in normal/navigation mode**, if available, and expose “Toggle sidebar” through your existing command menu or palette. Printable shortcuts must yield to text entry. Keep Ctrl+B as an optional alias and support user remapping.
2. **Keep Esc conventional; add Ctrl+G to leave insert mode**, subject to your existing keymap. Show `INSERT · Esc/Ctrl+G normal` while editing and update the mode indicator immediately when the event arrives.
3. **Document optional tmux tuning**, without requiring it or changing users’ configuration:
   ```tmux
   # ~/.tmux.conf — milliseconds
   set -s escape-time 10
   ```
   A very short timeout can misinterpret sequences arriving slowly over SSH, so avoid prescribing zero universally.
4. **Negotiate enhanced keyboard input where supported**, through your framework. It can disambiguate Esc, but support must survive the terminal → tmux → app path. Preserve legacy bindings.

To confirm the diagnosis, compare behavior outside tmux, check `tmux -V` and `tmux show-options -s escape-time`, and timestamp decoded key events in a file. Test lone Esc, Alt keys, arrows, and rapid typing after leaving insert mode.

For sidebar layout, let the main content win at **80×24**; at **60 columns**, open navigation as a single-pane view and restore focus on return. Truncate long labels and show a truthful message below your tested minimum. Keep help to one contextual hint row. Without a screenshot, border depth, redundant state markers, repeated row markers, and chrome usage cannot be counted reliably.