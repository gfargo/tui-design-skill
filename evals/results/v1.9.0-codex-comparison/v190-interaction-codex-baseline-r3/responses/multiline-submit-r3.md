Use **Enter to send**, with **Ctrl+J to insert a newline** as the reliable fallback. Support **Shift+Enter** where the terminal can distinguish it.

Traditional terminals often send the same bytes for Enter and Shift+Enter, so your TUI can’t reliably tell them apart. Modern keyboard protocols, such as Kitty’s, can distinguish them when supported and enabled.

A practical setup:

- **Enter:** send the message.
- **Ctrl+J:** insert a newline.
- **Shift+Enter:** insert a newline when supported.
- Show a hint: `Enter to send · Ctrl+J for newline`.

Handle multiline paste separately so pasted line breaks stay in the input and don’t trigger sending. Enable **bracketed paste** for this.

One caveat: Ctrl+J sends LF, while Enter usually sends CR. Make sure your input library preserves that distinction; some normalize both into the same Enter event.