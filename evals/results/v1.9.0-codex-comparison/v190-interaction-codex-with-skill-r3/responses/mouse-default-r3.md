**For a full-screen TUI with clickable targets, enable `1000 + 1002 + 1006`. Leave the inline picker’s mouse capture off.**

| Mode | Purpose | Recommendation |
|---|---|---|
| `1000` | Button presses/releases and wheel events | Enable for clicks and scrolling |
| `1002` | Pointer motion while a button is held | Enable for dragging; omit if unnecessary |
| `1006` | SGR mouse encoding, supporting large coordinates and identifying released buttons | Enable alongside reporting |
| `1003` | Every pointer movement | Only enable when hover behavior needs it |

Use the smallest reporting set your interface needs. Full-screen alone doesn’t justify capture if there are no mouse interactions.

For the full-screen app:

- Make every action keyboard-accessible.
- Provide `--no-mouse` or a configuration switch.
- Document how to select terminal text while capture is active: usually Shift, Option in iTerm2, or Fn in Terminal.app.
- Disable every mode you enabled on exit, errors, and suspend or external-program handoff; re-enable on resume. Prefer framework-managed cleanup.

**Keep the inline picker keyboard-driven** so ordinary text selection and terminal scrollback remain available. Give it visible navigation, accept, and cancel keys; send the selected result to stdout and interactive chrome to stderr or `/dev/tty`.