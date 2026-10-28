Use **50–60 terminal columns** as a default confirmation-dialog width, including borders and padding. Treat that as a guideline:

- Size short prompts to their content; wrap longer explanations.
- Cap the width at the terminal width minus 2–4 columns.
- Measure display cells, not string length—emoji and wide characters affect layout.
- On very narrow terminals, use a full-width panel and stack the buttons.

With **`NO_COLOR` set to a nonempty value**, keep the modal but remove foreground and background colors. Make its structure and focus clear through borders, spacing, text, and a visible selection marker:

```text
┌──────────────────────────────────────────────┐
│ Delete this project?                         │
│                                              │
│ This permanently deletes its local files.    │
│                                              │
│   > [Cancel]              [Delete project]    │
│                                              │
│ Tab: move   Enter: select   Esc: cancel       │
└──────────────────────────────────────────────┘
```

The modal should capture keyboard input, keep focus inside it, and restore focus when closed. Default destructive confirmations to **Cancel**. Don’t rely on a colored backdrop or red button to communicate modality or danger.

`NO_COLOR` doesn’t require disabling borders or bold, but the dialog should remain understandable in plain text.