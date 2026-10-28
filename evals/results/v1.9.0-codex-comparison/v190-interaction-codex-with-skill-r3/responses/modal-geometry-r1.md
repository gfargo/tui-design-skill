Use **60–80% of the terminal width**, with a **30-column minimum** and a cap of **about 80 columns for prose**. Count terminal cells, including borders and padding. Center horizontally, slightly above vertical center.

A practical default is:

```text
dialogWidth = min(terminalWidth - 4, 80,
                  max(30, round(terminalWidth * 0.70)))
```

That gives 56 columns at 80×24 and 42 columns in a 60-column tmux split. Wrap the message; keep the question and actions visible. If they cannot fit, show a “terminal too small” state and preserve cancellation.

With **non-empty `NO_COLOR`**, suppress automatic foreground/background colors, but keep the modal structure:

- Clear its rectangle before drawing so underlying text cannot bleed through.
- Use one border, an explicit title, and dialog-specific keyboard hints.
- Trap focus inside the dialog and restore prior focus when it closes.
- Mark the selected action with reverse video or a plain `>` marker.
- Treat background dimming as optional: faint is an attribute, and some terminals ignore it.

For example, the same monochrome structure works at both sizes:

```text
Wide terminal                       60-column split
+-----------------------------+     +-----------------------+
| Confirm deletion            |     | Confirm deletion      |
| Delete 3 files?             |     | Delete 3 files?       |
|                             |     |                       |
| > [Cancel]   [Delete]        |     | > [Cancel]  [Delete]   |
| Tab move  Enter choose      |     | Tab move  Enter choose|
| Esc cancel                  |     | Esc cancel            |
+-----------------------------+     +-----------------------+
```

Default destructive confirmations to **Cancel/No**. Keep chrome to that single border; extra nested boxes, warning icons, and repeated “Are you sure?” labels add noise without clarifying the decision.