Traditional terminals often send the same key sequence for **Enter** and **Shift+Enter**, so your TUI can’t distinguish them. tmux can also prevent the distinction from reaching the app.

To insert a newline:

- Try **Ctrl+J**—many TUIs bind it to newline while Enter submits.
- Check the app’s keybindings/help for “newline” or “insert line break.” Some use **Alt+Enter**.

For Shift+Enter itself to work, your terminal, tmux, and TUI must all support an extended keyboard protocol. On recent tmux versions, this setting may help:

```tmux
set -s extended-keys on
```

The terminal and app still need compatible support. Tell me which TUI, terminal, and tmux version you use, and I can give you the exact binding or configuration.