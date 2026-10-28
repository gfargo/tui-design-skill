Use **about 50 terminal columns** as the default for a confirmation dialog; **40–60 columns** usually works well.

- Size to the message and buttons, with 2 columns of horizontal padding.
- Cap width at the terminal width minus 2–4 columns.
- Wrap long messages; measure display cells rather than string length, especially for Unicode.
- On very small terminals, use the available width and stack buttons if necessary.

When `NO_COLOR` is set to a **nonempty value**, suppress color. You can still show a modal using structure and focus:

```text
┌─ Confirm deletion ───────────────────────────┐
│                                             │
│  Delete “report.csv”?                        │
│  This action cannot be undone.              │
│                                             │
│  > [ Cancel ]       [ Delete ]               │
└─────────────────────────────────────────────┘
```

Draw an opaque panel that clears the cells underneath, give it a visible border and title, and use a marker such as `>` for the focused button. Keep keyboard focus inside the modal, make Escape cancel, and restore focus when it closes. Default destructive confirmations to **Cancel**.

`NO_COLOR` doesn’t require disabling borders, cursor movement, or all text attributes, but the dialog should remain clear without color, bold, reverse video, or background dimming.