Both symptoms come from how terminal input reaches your app.

**Ctrl+B is tmux’s default prefix.** tmux consumes it while waiting for a tmux command, so your TUI never receives the key. With the default configuration, users can usually press **Ctrl+B twice** to send one Ctrl+B to the application—but that’s a workaround, not a good primary interaction.

**Esc is ambiguous in terminal input.** A standalone Escape key sends `ESC`, but arrow keys, function keys, and many Alt combinations also begin with `ESC`. tmux and your TUI’s input parser may wait briefly to determine which one arrived. Their delays can compound; network latency can make this more noticeable.

Design around that by:

- **Making shortcuts configurable**, including sidebar toggle and leaving insert mode.
- **Giving sidebar toggle another discoverable route**, such as a command palette entry and clickable control where mouse support exists. Avoid making Ctrl+B its only route.
- **Supporting an alternative to Esc**, commonly Ctrl+[. In traditional terminals it sends the same byte as Esc, so it’s familiar but **won’t necessarily eliminate the delay**. A distinct optional binding such as Ctrl+G can bypass that ambiguity.
- **Checking your input library’s Escape timeout.** Keep it short and configurable; use modern keyboard protocols where supported to distinguish keys more reliably, with a fallback for older terminals.

For tmux users, document this optional setting:

```tmux
set -sg escape-time 10
```

That sets tmux’s wait to 10 ms; `0` is also common locally. Very low values can misinterpret sequences that arrive slowly, so test over SSH as well. Changing tmux’s setting won’t fix a separate timeout inside your TUI.

The key product decision is to provide accessible alternatives by default, while treating terminal and multiplexer tuning as optional troubleshooting.