**This is a terminal input limitation: Shift+Enter is not always distinguishable from Enter.** Bubble Tea can only act on the key information it receives.

Traditional terminal input commonly encodes both keys as the same carriage-return byte (`\r`). Enhanced keyboard protocols, such as the Kitty keyboard protocol, can encode Enter together with its Shift modifier. That explains why it works in kitty when those enhancements are enabled.

Inside tmux, the whole path must preserve that information:

`terminal → tmux → Bubble Tea`

The terminal’s support alone is insufficient. tmux’s version, extended-key configuration, and negotiation with the application also matter. If any layer collapses Shift+Enter to plain Enter, Bubble Tea cannot reconstruct the missing modifier.

The design should be:

- **Enter sends; Shift+Enter inserts a newline when distinguishable.** Request Bubble Tea v2’s keyboard enhancements and match the actual key code and modifiers.
- **Always provide an alternate newline binding**, such as Ctrl+J, plus a discoverable command or configurable binding. Ctrl+J commonly arrives as line feed, distinct from Enter’s carriage return, though some configurations can still alias them.
- **Make help capability-aware.** Show Shift+Enter when enhanced key disambiguation is available; otherwise advertise the alternate binding. Successful negotiation helps, but does not prove every chord survives every terminal configuration.
- **Offer a multiline-friendly mode** where Enter inserts a newline and an explicit action sends. This avoids accidental submission for users whose terminal cannot distinguish the keys.
- **Keep pasted newlines as text.** Bracketed paste must not trigger the send action.

Don’t infer support from `$TERM`, kitty’s presence, or being outside tmux. Don’t use timing heuristics to guess Shift. When both keys produce identical bytes, the distinction is unavailable—not something an application-level key binding can fix.