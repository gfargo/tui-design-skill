Use a **quit ladder: one press handles one applicable step, then stops.**

| Priority | `Esc` action |
|---|---|
| 1 | Cancel the running request or operation; keep the previous data. |
| 2 | Close only the topmost modal, menu, help screen, or completion popup. |
| 3 | Clear the active filter, search, or multi-selection. Cancelling search restores the prior position. |
| 4 | Back out one drill-down level or escape a focus trap. |
| 5 | At the root, do nothing. **Esc never quits.** |

Give the other keys distinct roles:

- **`q`:** Back one level when nested; quit at the root. While a text field owns input, insert `q`.
- **`Ctrl+C`:** Cancel a running operation first. With nothing running, quit from anywhere without walking the ladder.

Guard against actual loss: confirm a root-level `q` when edits or non-resumable work would be lost, defaulting to No. For `Ctrl+C`, show `Unsaved changes. Press Ctrl+C again to quit`; a second press within about two seconds exits. Idle quits need no confirmation.

Consume each handled event so one Esc cannot close a popup, clear a filter, and navigate back together. Route every quit through the same terminal cleanup.

Show the current meaning in a compact footer: `Esc clear filter · q back · Ctrl+C quit`.