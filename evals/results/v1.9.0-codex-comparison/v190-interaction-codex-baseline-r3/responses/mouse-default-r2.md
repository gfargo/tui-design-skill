For a **full-screen TUI**, enable:

- **1000 — normal tracking** if you only need clicks and scrolling.
- **1002 — button-event tracking** instead if you also need dragging. This is a good default for resizable panes, scrollbars, and text selection.
- **1006 — SGR extended coordinates** alongside either mode. It avoids legacy coordinate limits and clearly identifies button releases.

Use **1003 — all-motion tracking** only when you actually need hover or pointer movement with no button held. It can generate substantial input traffic.

For example, enable dragging plus SGR reporting with:
```text
ESC[?1002h ESC[?1006h
```
Disable the modes you enabled on exit, and disable reporting while suspended. Keep keyboard equivalents for mouse actions; document the terminal’s selection override, commonly Shift+drag.

For an **inline picker, default to no mouse reporting**. Reporting applies to the terminal, not just the picker’s rows, so it can interfere with selecting text, scrolling, and interacting with shell history. Use arrow keys, typing to filter, Enter, and Escape. If mouse interaction is central to the picker, consider presenting it as a full-screen interface instead.