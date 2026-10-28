Inside tmux, **Shift+Enter often arrives as plain Enter**, so your TUI can’t distinguish them.

Try **Ctrl+J**: it sends a line-feed character, which some TUIs use for a newline. If it also submits, the app needs a separate newline binding.

If you’re implementing the TUI:

- Bind newline insertion to **Ctrl+J** or another explicit shortcut.
- For **Shift+Enter**, enable an extended keyboard protocol supported by your terminal, tmux, and TUI library.
- On recent tmux versions, this setting can help:
  ```tmux
  set -s extended-keys on
  ```
  It works only when the terminal and application also support extended keys.

Which TUI or input library are you using? The exact newline shortcut and configuration depend on it.