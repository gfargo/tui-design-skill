Treat terminal theme detection as a **best-effort, asynchronous hint**, never a prerequisite for startup. The terminal’s background is what matters for readability; it may differ from the OS theme.

A good design has these parts:

- **Offer `auto`, `light`, and `dark` settings.** An explicit choice takes precedence over detection. In `auto`, use a documented fallback when detection fails.
- **Render immediately using the fallback.** Send the background-color query—usually OSC 11—through the terminal connection, and handle the reply through your normal input parser. Use a short deadline, roughly 100–300 ms; never block startup waiting for it. SSH adds latency, and some terminals or multiplexers never return a reply.
- **Parse replies as terminal protocol messages.** They arrive in the same stream as keyboard input and may be fragmented. Accept the supported color formats and terminators, bound response lengths, and keep malformed or unrelated input from being swallowed. A valid late reply can still update the theme.
- **Classify the returned color using luminance.** Convert sRGB to linear RGB before computing relative luminance; don’t just average the channel values. If you re-evaluate repeatedly, use hysteresis near the threshold to avoid flickering between themes.
- **Subscribe to theme changes when supported.** Some terminals implement color-scheme change notifications, such as private mode 2031. Detect support, enable notifications for the session, and disable them during cleanup. OSC 11 itself is a query, not a subscription.
- **Use bounded rechecks as a fallback.** Requery after resume or terminal focus gain, where available. In terminals without notifications, detecting changes requires polling; keep it infrequent and allow only one outstanding query.

Keep the deadline and reply handling inside one terminal-protocol layer, with tests for no reply, delayed and fragmented replies, malformed responses, and ordinary input interleaved with responses.

The practical contract is: **startup always proceeds, explicit settings always win, and automatic colors update when the terminal provides enough information.** Reliable OS-theme tracking cannot be promised over SSH or across all terminals.