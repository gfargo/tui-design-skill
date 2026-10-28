Use **Esc to unwind, q to back out, and Ctrl+C to interrupt or exit.** Each keypress should perform one action and stop.

| Priority | When… | Esc does… |
|---|---|---|
| 1. Cancel | An operation is running | Cancel it; retain the previous data |
| 2. Close | An overlay, menu, or completion popup is open | Close only the topmost one |
| 3. Clear | A search, filter, or multi-selection is active | Clear it; cancelled search restores the prior position |
| 4. Back | Inside a detail view, drill-down, or focus trap | Return one level |
| 5. Root | None of these applies | Nothing—Esc never quits |

**Change your global `q` binding:** in a nested view, it goes back one level; at the root, it quits. When a text field owns input, `q` types a letter.

**Ctrl+C bypasses navigation:** cancel running work first; with nothing running, quit from anywhere. If quitting would lose edits or non-resumable work, show `Press Ctrl+C again to quit`; a second press within about two seconds exits. For `q`, use a loss-specific confirmation with **No** as the default. Idle quits need no confirmation.

Consume handled events so one Esc cannot cancel a job, dismiss a dialog, and navigate back together. Route every exit through the same terminal cleanup.

Keep the footer contextual: `Esc close · q back · Ctrl+C quit`, changing those labels to reflect the current action.