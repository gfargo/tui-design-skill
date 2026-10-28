Use a predictable ladder: **Esc unwinds local state, q backs out, Ctrl+C interrupts or exits.**

For **Esc**, handle the first applicable step, then consume the event:

| Priority | Condition | Action |
|---|---|---|
| 1 | An operation is running | Cancel it; retain the previous data |
| 2 | An overlay is open | Close only the top modal, menu, palette, help, or completion popup |
| 3 | Search, filter, or multi-selection is active | Clear it; cancelled search restores the prior position |
| 4 | Inside a nested view or focus trap | Go back one level |
| 5 | At the root | Do nothing—Esc never quits |

**q:** While typing, insert `q`. Otherwise, go back one level; quit only at the root. Replace your current “quit from anywhere” binding.

**Ctrl+C:** Cancel a running operation first. With nothing running, quit from anywhere. If quitting would lose work, show `Press Ctrl+C again to quit`; a second press within about two seconds exits. An idle, lossless quit needs no confirmation.

Keep meaningful edits protected when closing or backing out, too. Route every actual exit through the same terminal cleanup.

Show the current action in the footer—for example, `Esc close · q back` in a nested overlay and `q quit` at the root. **One keypress must cause one transition**, never close a popup, clear a filter, and navigate back through event bubbling.