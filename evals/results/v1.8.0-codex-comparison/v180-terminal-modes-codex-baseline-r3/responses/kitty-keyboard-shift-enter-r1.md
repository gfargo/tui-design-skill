This is a terminal protocol limitation: **the app can distinguish keys only if the terminal sends different input for them.**

In traditional terminal input, Enter usually sends carriage return (`\r`). Shift+Enter often sends exactly the same byte. By the time Bubble Tea receives it, the Shift information is gone; no key binding can recover it.

Kitty’s enhanced keyboard protocol can encode Enter together with its modifiers. Bubble Tea v2 can interpret those events when the appropriate keyboard enhancements are enabled and supported. Inside tmux, the whole path matters: the terminal, tmux’s version and extended-key configuration, and the application must cooperate. Support in the outer terminal alone is insufficient.

The design should be:

- **Enter sends.** Handle submission explicitly, before forwarding the event to the textarea.
- **Shift+Enter inserts a newline when reported distinctly.** Match the parsed key and modifiers rather than raw escape sequences.
- **Provide an always-advertised alternative**, such as Ctrl+J. It commonly sends line feed (`\n`), distinct from Enter’s carriage return. Verify that your input handling preserves that distinction.
- **Treat pasted text as text.** A multiline paste should populate the composer, never trigger submission because it contains newlines.
- **Offer configurable bindings**, including an Enter-for-newline mode for users who prefer it.

Request keyboard enhancements through Bubble Tea’s supported mechanism, but don’t infer reliable Shift+Enter support from `$TERM`, “running in kitty,” or a protocol response alone. Those don’t guarantee that the complete path preserves that particular key.

A useful hint is **“Enter send · Ctrl+J newline”**, with Shift+Enter documented as another newline shortcut where supported. If Shift+Enter arrives as ordinary Enter, it necessarily sends under this design. If preventing that accidental send is a hard requirement, use Enter for newline and a separate explicit send shortcut.