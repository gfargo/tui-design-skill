**For a full-screen TUI with clickable targets, enable `1000 + 1002 + 1006`. Keep the inline picker’s mouse reporting off.**

| Mode | Purpose | Recommendation |
|---|---|---|
| `1000` | Button press/release and wheel events | Enable for clicks and scrolling |
| `1002` | Motion while a button is held | Enable for dragging; omit if unused |
| `1006` | SGR mouse encoding: larger coordinates and explicit released button | Enable alongside reporting |
| `1003` | Every pointer movement | Enable only when hover behavior needs it |

`1006` controls encoding; it doesn’t enable reporting by itself. Use the smallest reporting set your interface needs.

Mouse capture takes over normal text selection. Provide `--no-mouse` or a configuration switch, keep every action keyboard-accessible, and document the selection bypass: usually Shift, Option in iTerm2, or Fn in Terminal.app. Disable enabled modes on every exit and temporary terminal handoff; restore them on resume, preferably through your framework’s lifecycle support.

**Leave the inline picker keyboard-driven** so terminal selection and scrollback remain usable. Show its complete controls inline, such as `↑/↓ move · Enter choose · Esc cancel`. Send interactive chrome to stderr or `/dev/tty`, and only the selected result to stdout.