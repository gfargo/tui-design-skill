**Size confirmation dialogs to their content, capped at 60–80% of terminal width.** Aim for at least 30 columns and no more than about 80 columns for prose, including room for borders and padding. Center horizontally, slightly above vertical center.

For a short confirmation, 36–48 columns is usually enough. At 80×24, a 48-column dialog works well; in a 60-column tmux split, keep it within 36–48 columns and wrap the message. On resize, preserve the question and controls; if they cannot fit, show a truthful “terminal too small” state.

**With non-empty `NO_COLOR`, keep the modal and suppress automatic colors.** Make its structure communicate modality:

- Clear the rectangle behind it with blank cells so underlying text cannot bleed through.
- Draw one border and an explicit title.
- Use a text focus marker such as `>` and show the active controls.
- Trap keyboard focus; `Esc` cancels, then restores the previous focus.
- Treat faint background dimming as optional: some terminals ignore it.

These monochrome sketches work at both sizes:

```text
80-column terminal                 60-column terminal
        +-- Confirm deletion --------+   +-- Confirm deletion --------+
        | Delete 3 files?            |   | Delete 3 files?            |
        |                            |   |                            |
        | > [Cancel]    [Delete]     |   | > [Cancel]    [Delete]     |
        | Tab move  Enter choose     |   | Tab move  Enter choose     |
        | Esc cancel                 |   | Esc cancel                 |
        +----------------------------+   +----------------------------+
```

Default destructive confirmations to **Cancel/No**. Use a typed target name for high-consequence actions such as deleting a production database.

Keep the chrome lean: one border, no nested boxes, and no repeated warning icons. The title, focus marker, and controls should remain clear with both color and faint styling disabled.