Use **3–5 seconds for routine status messages**, and keep errors visible until the user has a chance to act.

| Message | Recommended behavior |
|---|---|
| Routine success (“Saved”) | Clear after 3 seconds |
| Informational message | Show for 5 seconds; longer if it needs reading |
| Work in progress | Keep visible until completion; replace with the result |
| Warning requiring a decision | Keep until resolved or dismissed |
| Error | Keep until dismissed, corrected, or superseded by a relevant result |

For errors:

- Say **what failed and what the user can do next**: “Save failed: permission denied. Choose another path.”
- Don’t let routine updates overwrite them.
- Preserve them in a scrollback, log, or message history so dismissal doesn’t lose the details.
- Use a label or icon as well as color.
- Avoid modal dialogs unless continuing requires a decision.

A useful default: **success fades; errors stick; all messages remain recoverable.**