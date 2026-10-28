Keep **Enter to send**, and offer **Ctrl+J to insert a newline** as the dependable fallback. Show a small hint near the input:

`Enter send · Ctrl+J newline`

Support **Shift+Enter** wherever the terminal can distinguish it. Traditional terminals often encode Enter and Shift+Enter identically, so your TUI can’t reliably tell them apart. Enhanced keyboard protocols, such as Kitty’s, can distinguish them when supported by both the terminal and your TUI library.

Also:

- Treat bracketed paste as text insertion, so pasted newlines never trigger sending.
- Let users configure the send and newline bindings.
- Consider an optional multiline mode where Enter adds a newline and another shortcut sends.

Check how your input library normalizes keys: Ctrl+J usually arrives as LF (`\n`), while Enter usually arrives as CR (`\r`), but some configurations merge them.