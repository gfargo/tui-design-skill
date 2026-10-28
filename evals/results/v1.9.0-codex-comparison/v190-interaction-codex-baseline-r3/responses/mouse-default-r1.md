For a full-screen TUI, enable **button-event tracking (`1002`) plus SGR mouse encoding (`1006`)** if you support dragging:

```text
Enable:  ESC[?1002h ESC[?1006h
Disable: ESC[?1002l ESC[?1006l
```

Choose the tracking mode based on actual behavior:

| Mode | Reports | Use when |
|---|---|---|
| `1000` | Button presses, releases, and wheel events | Clicking and scrolling are enough |
| `1002` | Above, plus motion while a button is held | You support dragging or resizing |
| `1003` | Above, plus all mouse motion | You need hover behavior; otherwise avoid the event traffic |

`1006` controls event encoding; enable it alongside your chosen tracking mode for reliable coordinates and button information. Avoid legacy X10 mode (`9`) and UTF-8 coordinate encoding (`1005`) for new implementations.

Restore mouse settings on exit, errors, and suspension; re-enable them on resume. Keep every action keyboard-accessible, and remember that mouse capture interferes with normal terminal text selection.

**An inline picker should generally leave mouse reporting off.** Let the terminal handle selection and scrollback, and use arrows, typing, Enter, and Escape for the picker. Mouse reporting applies to the terminal, not just the picker’s rows, so even a small inline widget can capture clicks and wheel events elsewhere. Add it only as an explicit opt-in when the interaction meaningfully benefits from it.