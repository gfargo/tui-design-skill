Use **the most local action first**, with one action per keypress.

| Key | Priority |
|---|---|
| **Esc** | Dismiss a popup → cancel the current edit or mode → close the active dialog → go back one level. At the root, do nothing. |
| **q** | Quit only from the root’s normal navigation mode. In text fields, type `q`; in nested views, avoid making it a global quit shortcut. |
| **Ctrl+C** | Interrupt a running operation first. If nothing is running, request application exit, confirming if work would be lost. |

For your five Esc behaviors, resolve them against **the deepest active layer**. Once that layer handles Esc, consume the event: closing a popup must not also close its parent dialog.

Keep a visible hint matched to the current context: `Esc close`, `Esc cancel edit`, `Esc back`, or `q quit`. Avoid requiring users to remember what Esc means in each state.