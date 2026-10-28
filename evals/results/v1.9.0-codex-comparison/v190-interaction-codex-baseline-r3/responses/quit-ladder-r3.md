Use one consistent rule: **Esc backs out one layer, q quits only at the root, and Ctrl+C interrupts work before it exits.**

Handle keys from the innermost active layer outward:

| Active context | Esc | q | Ctrl+C |
|---|---|---|---|
| Text input | Cancel editing or restore prior value | Type `q` | Cancel current operation |
| Popup, menu, or dialog | Close/cancel the topmost layer | Follow dialog bindings; never global quit | Cancel current operation |
| Selection or special mode | Leave that mode | No global quit | Cancel current operation |
| Nested screen | Return to parent | No global quit | Cancel running work; otherwise request exit |
| Root screen | Clear transient state; otherwise no-op | Request exit | Request exit |

Each keypress should trigger **one action**, then stop propagating. An Esc that closes a popup must not also navigate back.

For your five Esc actions, prioritize: **topmost overlay → active edit/mode → transient selection/filter → parent screen → root no-op**. Follow visible nesting if those states overlap.

Route every exit request through the same unsaved-work check. If you support a second Ctrl+C to force exit, make that behavior explicit after the first press.