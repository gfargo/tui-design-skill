Size confirmation dialogs to their content, with a sensible cap:

- **Typical width:** 50–60 terminal columns, including borders and padding.
- **Short prompts:** 35–45 columns is often enough.
- **Responsive limit:** `width = min(preferred_width, terminal_width - 4)`. On very narrow terminals, reduce margins and stack buttons.
- Wrap long messages and paths; keep the action buttons visible.

For destructive actions, name the consequence and use explicit buttons, such as **Cancel** and **Delete file**. Default focus to the safer action.

When `NO_COLOR` is set, preserve the modal’s structure and behavior; remove color styling. Make it distinct through:

- A solid, opaque background that hides underlying text.
- A visible border, title, and whitespace.
- A color-independent focus marker, such as `> [Cancel]`.
- Keyboard focus trapped inside the modal, with Escape cancelling.

```text
┌─ Delete file? ────────────────────────────┐
│                                          │
│ Delete “report.csv”?                     │
│ This cannot be undone.                   │
│                                          │
│           > [Cancel]    [Delete file]    │
└──────────────────────────────────────────┘
```

Treat any **nonempty** `NO_COLOR` value as enabled, including `NO_COLOR=0`. It disables color, not necessarily bold or other attributes—but the dialog should remain understandable without them.