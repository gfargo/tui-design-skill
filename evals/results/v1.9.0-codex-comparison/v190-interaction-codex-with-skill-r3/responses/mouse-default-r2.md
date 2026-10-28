**For the full-screen TUI, enable the smallest mouse reporting mode your interactions need, plus SGR encoding (`1006`). Leave mouse capture off in the inline picker.**

| Mode | Reports | When to enable |
|---|---|---|
| `1000` | Button presses/releases and wheel events | Clicks and scrolling |
| `1002` | Adds movement while a button is held | Drag selection, pane resizing, sliders |
| `1003` | Every pointer movement | Only for actual hover behavior |
| `1006` | SGR mouse encoding | Pair with your chosen reporting mode; supports coordinates past column 223 and identifies released buttons |

A typical full-screen app with draggable targets uses **`1000` + `1002` + `1006`**. Skip `1003` unless you consume hover events; it generates traffic on every move.

Mouse capture takes over normal terminal text selection. Provide `--no-mouse` or a config switch, document the terminal’s selection-bypass modifier—it isn’t always Shift—and keep every action keyboard-accessible. Disable all modes you enable on exit, errors, and suspend or subprocess handoff; re-enable them on resume.

**Your inline picker should use the keyboard**, preserving terminal selection and scrollback. Show its compact controls, such as `↑/↓ move · Enter choose · Esc cancel`, keep interactive chrome on stderr or `/dev/tty`, and emit only the selected result on stdout.