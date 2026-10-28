Use message importance to set the lifetime:

| Message | Recommended behavior |
|---|---|
| Routine success (“Saved”) | Show for **3–5 seconds**, then clear. |
| Informational notice | Show for **5–8 seconds**, or until the next relevant action. |
| Progress (“Syncing…”) | Keep visible until the operation finishes; replace with its result. |
| Warning | Keep until resolved or dismissed if the user needs to act. |
| Error | **Don’t auto-dismiss.** Keep until acknowledged, resolved, or superseded by a successful retry. |

For errors, say **what failed and what the user can do next**: “Save failed: permission denied. Choose another path or retry.” Preserve the user’s input and current context.

Let users dismiss messages with a consistent key, and keep errors in a discoverable message history. Routine success messages shouldn’t overwrite an unresolved error. If work can continue, keep the error in the status line; use a dialog only when the failure blocks progress or requires a decision.

Timers should start when the message actually becomes visible, and important information should never be available only through a timed message.