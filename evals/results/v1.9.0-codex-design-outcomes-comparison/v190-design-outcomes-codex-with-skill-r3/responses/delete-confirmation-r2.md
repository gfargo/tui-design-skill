Make the scope explicit: **delete the 14 marked files**, with **No as the default**. Assuming `d` permanently deletes:

80-column terminal; centered dialog over the file list:

```text
        +--------------------------------------------------------------+
        | Delete 14 marked files?                                      |
        |                                                              |
        | Only the 14 marked files out of 3,000 will be deleted.        |
        | This permanently deletes them. You cannot undo this.         |
        |                                                              |
        | y Delete     n / Enter / Esc Cancel                          |
        +--------------------------------------------------------------+
```

- `y`: delete exactly the 14 files marked when the dialog opened.
- `n`, `Enter`, `Esc`, or `q`: cancel; preserve marks, cursor, and scroll position.
- `Ctrl+C`: cancel this confirmation.
- `Ctrl+Z`: suspend; restore the dialog on resume.
- Other keys, including another `d`: do nothing. The underlying list receives no input.

At 60 columns, keep the same confirmation and wrap the text:

```text
  +------------------------------------------------------+
  | Delete 14 marked files?                              |
  |                                                      |
  | Only the 14 marked files out of 3,000                 |
  | will be deleted.                                     |
  | This permanently deletes them.                       |
  | You cannot undo this.                                |
  |                                                      |
  | y Delete     n / Enter / Esc Cancel                   |
  +------------------------------------------------------+
```

At 80×24, the list remains visible behind the modal. At smaller sizes, hide the background first; if the warning and controls cannot fit, block deletion and show “Resize to confirm; Esc cancels.”

Clutter audit: one border, no per-file markers or repeated filename rows, and no color required. The border and padding use about a quarter of the dialog’s cells.

If `d` actually moves files to Trash, label the action **“Move 14 marked files to Trash?”** and describe its real recovery behavior.