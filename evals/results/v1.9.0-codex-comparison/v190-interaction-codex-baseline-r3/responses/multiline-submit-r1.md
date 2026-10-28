Use **Enter to send**, with **Ctrl+J to insert a newline** as a documented fallback. Support Shift+Enter wherever the terminal can distinguish it.

Traditional terminals often send the same bytes for Enter and Shift+Enter, so your TUI can’t reliably tell them apart. Modern keyboard protocols, such as Kitty’s, can distinguish them when supported by both the terminal and your TUI library.

A practical setup:

- **Enter:** send.
- **Shift+Enter:** newline when distinguishable.
- **Ctrl+J:** newline fallback. Verify your input library preserves the distinction between LF (`Ctrl+J`) and CR (`Enter`).
- **Pasted multiline text:** preserve newlines; use bracketed paste so pasted Enter characters don’t trigger sending.

Show a hint such as `Enter send · Ctrl+J newline`. For users whose terminal or input library collapses those keys too, offer a configurable mode where Enter inserts a newline and an explicit command or shortcut sends.