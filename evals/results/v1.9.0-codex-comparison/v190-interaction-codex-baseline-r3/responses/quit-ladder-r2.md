Use a consistent rule: **Esc backs out one layer, q quits from the main screen, Ctrl+C interrupts or exits.**

Handle Esc from the innermost active layer outward:

1. Dismiss transient UI: tooltip, completion menu, popover.
2. Cancel the current interaction: search, edit, selection, key sequence.
3. Close the active dialog or modal.
4. Leave the detail view or nested screen.
5. At the main screen, do nothing.

Each press should perform **one action**, never cascade through multiple layers. If backing out would lose work, show a discard prompt.

For the other keys:

| Key | Recommended behavior |
|---|---|
| **q** | Quit from the main screen only. In text inputs, type `q`; elsewhere, avoid a global quit binding. |
| **Ctrl+C** | Cancel a running operation first. When idle, request application exit; protect unsaved work with a prompt. |

Show context-specific hints such as `Esc Cancel`, `Esc Back`, or `q Quit`. If Ctrl+C cancels an operation, say so explicitly so users understand why the app stayed open.