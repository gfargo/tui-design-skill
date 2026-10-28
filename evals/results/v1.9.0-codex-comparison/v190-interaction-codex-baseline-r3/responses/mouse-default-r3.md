For a full-screen TUI, enable **SGR mouse encoding (`1006`) plus the least mouse tracking your UI needs**:

| Mode | Reports | Use when |
|---|---|---|
| `1000` | Button presses/releases and wheel events | You need clicks and scrolling |
| `1002` | Those events plus movement while a button is held | You support dragging, resizing panes, or text selection |
| `1003` | All pointer movement, even without a button held | You actually implement hover behavior |

**A good default is `1002` + `1006`** for a full-screen app with dragging; use `1000` + `1006` if it only needs clicks and scrolling. `1006` controls the event encoding—it does not enable tracking by itself. Avoid enabling `1003` speculatively: it produces constant motion events.

Enable reporting while your full-screen UI is active, and disable the modes you enabled on exit and before suspending or handing control to another program. Keep keyboard navigation complete, offer a mouse-off option, and preserve a way to use native terminal selection—often Shift-drag, depending on the terminal.

**An inline picker should generally leave mouse reporting off.** It shares the terminal with scrollback and ordinary text, where users expect selection, copying, and wheel scrolling to work normally. Mouse reporting can capture those actions across the terminal, not just inside the picker.

If mouse interaction is essential to the picker, make it explicit opt-in, enable it only while the picker is active, and reliably restore terminal state afterward. Otherwise, use arrow keys, typing to filter, Enter, and Escape.