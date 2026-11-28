Make the scope explicit: **`d` acts on the 14 marked files**, regardless of which row has the cursor. Default to Cancel. Assuming deletion is permanent:

80-column terminal; confirmation overlays the file list:
```text
        +--------------------------------------------------------------+
        | Delete 14 marked files?                                      |
        |                                                              |
        | Only the 14 marked files will be deleted.                     |
        | The other 2,986 files will remain.                            |
        |                                                              |
        | This permanently deletes the files. Cannot be undone.        |
        |                                                              |
        | y Delete 14 files    Enter/n/Esc Cancel                       |
        +--------------------------------------------------------------+
```

Keys while the confirmation is open:

- **`y`**: delete exactly the 14 files captured when `d` was pressed.
- **`Enter`, `n`, `Esc`, `q`**: cancel; return to the same cursor position with all 14 marks preserved.
- **`Ctrl+C`**: interrupt the confirmation and exit cleanly.
- **`d` and other ordinary keys**: no action. Repeating the initiating key cannot confirm.

The modal owns input; background navigation and marking are paused. If the target set changes before confirmation, report the change and require a fresh confirmation.

At 60 columns, keep the count, consequence, and controls:
```text
    +--------------------------------------------------+
    | Delete 14 marked files?                          |
    |                                                  |
    | 2,986 other files will remain.                   |
    | Permanent deletion. Cannot be undone.            |
    |                                                  |
    | y Delete 14 files                                |
    | Enter/n/Esc Cancel                               |
    +--------------------------------------------------+
```

At 80×24 both layouts fit comfortably. Below 40×10, show “Terminal too small; resize or Esc to cancel” and disable confirmation.

Clutter audit: one border, no nested boxes, icons, or repeated row markers. Text carries every meaning without color.

If the operation uses Trash, replace “permanently deletes” with “moves to Trash” and label the action **Move 14 files to Trash**.