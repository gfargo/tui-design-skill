Try **Ctrl+J** or **Alt+Enter**—common newline shortcuts in TUIs, though the exact binding depends on the app.

Many terminals send the same key sequence for **Enter** and **Shift+Enter**, so the TUI can’t distinguish them. tmux can also prevent extended key information from reaching the app.

If you’re building the TUI, provide an explicit newline binding such as **Ctrl+J** alongside Shift+Enter. Shift+Enter requires compatible keyboard-protocol support across the terminal, tmux, and your input library.

Which TUI and terminal are you using?