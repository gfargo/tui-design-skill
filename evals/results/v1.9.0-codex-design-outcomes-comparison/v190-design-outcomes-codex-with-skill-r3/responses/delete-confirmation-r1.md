Confirm deletion of the **14 marked files**, regardless of the cursor position. Default to **No**. Assuming `d` permanently deletes files:

80-column terminal; example filenames:

```text
Files: /home/alex/downloads                       3,000 files | 14 marked

        +--------------------------------------------------------------+
        | Delete 14 marked files?                                      |
        |                                                              |
        | Permanently delete these files. This cannot be undone.       |
        | The other 2,986 files will remain.                            |
        |                                                              |
        | Marked files (1-4 of 14):                                     |
        |   archive.zip                                                |
        |   draft.txt                                                  |
        |   export.csv                                                 |
        |   notes.old                                                  |
        |                                                              |
        | Up/Down scroll marked files                                  |
        | y delete 14 files    n/Enter/Esc cancel                       |
        +--------------------------------------------------------------+
```

- **`y`**: delete exactly the 14 files captured when the prompt opened.
- **`n`, `Enter`, `Esc`, `q`**: cancel; preserve marks, cursor, and scroll position.
- **`Up` / `Down`, `PgUp` / `PgDn`, `Home` / `End`**: review the marked files without changing the selection.
- **`Ctrl+C`**: exit the file manager without deleting.
- **`d` and other keys**: do nothing while the confirmation is open. Repeating `d` cannot confirm.

At 80×24, keep the list visible behind this focus-trapping dialog. In a 60-column split, use the same single-dialog layout with fewer preview rows:

```text
  +------------------------------------------------------+
  | Delete 14 marked files?                              |
  | Permanently delete. Cannot be undone.                |
  | Other 2,986 files remain.                            |
  |                                                      |
  | Marked files (1-2 of 14):                             |
  |   archive.zip                                        |
  |   draft.txt                                          |
  |                                                      |
  | Up/Down scroll marked files                          |
  | y delete 14 files    n/Enter/Esc cancel               |
  +------------------------------------------------------+
```

Truncate long paths in the preview and reveal the full focused path on a wrapped detail line. Below 60×16, show “Confirmation needs 60×16; resize or Esc to cancel” and disable deletion.

Clutter audit: one border, no repeated row markers, no color dependency; roughly half the dialog is framing and instructions, with the rest reserved for scope and file review. If `d` moves files to Trash, say **“Move 14 marked files to Trash?”** and describe recovery instead of claiming permanence.