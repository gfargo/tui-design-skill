`INK_SCREEN_READER=true` changes how Ink writes terminal output; it doesn’t turn the app into a semantic live region or decide which updates deserve announcements.

In screen reader mode, Ink avoids its usual cursor-based redraws and emits updated output as readable text. If your conversation lives in the dynamic render tree, each spinner tick or streamed token can cause the conversation to be emitted again. NVDA then encounters that text as new output. Giving the spinner a fixed label doesn’t stop those updates.

Change the screen reader experience in three ways:

- **Append completed messages once.** Put finalized conversation messages in Ink’s `<Static items={messages}>`, with stable IDs and immutable entries. Keep historical messages out of the dynamic area.
- **Stop animation and token-by-token output.** In screen reader mode, unmount the spinner so its timer stops. Buffer the response and emit it when complete, or emit deliberate sentence-sized chunks once.
- **Announce meaningful state changes once.** Output “Assistant is responding” when a request starts, then the answer or error when it finishes. Avoid repeatedly rendering the same status beside changing content.

Keep the animated, streaming UI for visual mode, and select the accessible rendering path using Ink’s screen reader detection. `<Static>` is for append-only content; don’t put a partially streamed message there and keep editing it.

Verify with NVDA in the users’ actual terminal: one submitted message, one start announcement, one completed answer, and no output while merely waiting. Include retries, errors, and a second conversation turn.

I couldn’t inspect your app or retrieve Ink’s source in this environment, so the exact trigger still needs confirmation. The key thing to check is whether spinner ticks and token updates are re-emitting the entire dynamic transcript.