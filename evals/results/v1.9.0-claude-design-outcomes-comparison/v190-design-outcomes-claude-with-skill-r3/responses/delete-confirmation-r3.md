The dialog moves the marked items to Trash, defaults to Cancel, and lists what will go. 11 of the 14 marks are probably scrolled out of view among the 3,000 rows, so the user can't check them any other way.

## The sketch (80×24)

```
 ~/photos/2024                                          14 marked · 3,000 items
   DSC_0001.NEF                                                      24.0 MB
   DSC_0 ┌─ Delete 14 marked items? ──────────────────────────────────┐ 24.2 MB
 * DSC_0 │                                                            │ 24.1 MB
   DSC_0 │  Move 13 files and 1 folder (212 files inside) to Trash    │ 23.7 MB
   DSC_0 │  1.7 GB total · 11 of the 14 are off-screen                 │ 24.3 MB
   DSC_0 │                                                            │ 23.9 MB
   DSC_0 │    build/  (folder, 212 files)                     1.2 GB  │ 24.0 MB
 * DSC_0 │    wedding-panorama-sti…hed-full.tif             412.0 MB  │ 23.6 MB
   DSC_0 │    DSC_0102.NEF                                   24.4 MB  │ 24.1 MB
   DSC_0 │    DSC_0003.NEF                                   24.1 MB  │ 23.5 MB
   DSC_0 │    DSC_0021.NEF                                   23.8 MB  │ 24.2 MB
   DSC_0 │    DSC_0008.NEF                                   23.6 MB  │ 23.8 MB
   DSC_0 │    IMG_0412.jpg                                    3.1 MB  │ 24.0 MB
   DSC_0 │    ↓ 7 more, all under 3 MB (j/k scroll)                   │ 23.9 MB
   DSC_0 │                                                            │ 24.4 MB
   DSC_0 │  Recoverable from Trash, or press u right after.           │ 23.7 MB
   DSC_0 │                                                            │ 24.1 MB
   DSC_0 │        [y] Move to Trash      [N] Cancel (Enter, Esc)      │ 24.0 MB
   DSC_0 └────────────────────────────────────────────────────────────┘ 23.9 MB
   DSC_0020.NEF                                                      24.0 MB
 * DSC_0021.NEF                                                      23.8 MB
   DSC_0022.NEF                                                      24.2 MB
 DELETE  y move to Trash   n/Esc/Enter cancel   j/k scroll list
```

The list behind the dialog is dimmed where the terminal supports it. The border, the title and the changed footer still mark it as a dialog without dimming or color, for example under `NO_COLOR`.

## What each key does

| Key | Action |
|---|---|
| `y` (or `Y`) | Moves all 14 items to Trash, clears the marks, and keeps the cursor near the same row. The status line then shows `Moved 14 items to Trash · u undo`. |
| `n`, `Esc`, `Enter` | Cancel. The dialog closes, the 14 marks stay, and nothing moves. `Enter` cancels because the default is No, so pressing Enter out of habit never deletes anything. |
| `Ctrl+C` | Also cancels. While this dialog is open it does not quit the app. |
| `j`/`k`, `↓`/`↑` | Scroll the list of items in the dialog. `PgDn`/`PgUp` jump a page. |
| `d` | Does nothing. A double-tap or key repeat on `d` can't confirm the delete. Any other unbound key also does nothing and leaves the dialog open. |
| `u` (after `y`) | Restores the items from Trash, as long as the delete is still the most recent action. |

## Why it looks like this

- **It says "marked".** `d` acts on the 14 marks, not on the row under the cursor. The title says so, and that matters when the cursor sits on an unmarked file.
- **It lists the items** because most of them are off-screen. The list is sorted by size, largest first, so the items with the biggest impact are always visible, and the hidden "7 more" are the least important.
- **It counts what's inside folders.** "14 items" hides 212 files inside `build/`. The summary line and that row both show the real count.
- **The confirmation is a light y/N.** Trash and `u` make this delete recoverable, so a typed confirmation would add friction without adding safety.
- **Long names are cut in the middle** (`sti…hed-full.tif`) so the file extension stays visible.

## Variants

- **Trash is unavailable** (for example a network mount or another volume): the title becomes `Permanently delete 14 items?`, the recovery line becomes `This cannot be undone.`, and confirming means typing `delete` instead of pressing `y`. A permanent delete of a 212-file folder warrants the heavier step.
- **Some marks are hidden by an active filter:** the summary line says `3 are hidden by the current filter`. Deleting something the user can't see without being told is the worst outcome here.
- **Type-ahead:** the dialog discards any keys that were already buffered when it opened.

## Clutter audit

- There is one border, the dialog's own.
- The `*` mark is left off the dialog's rows. Every row in it is marked, so the symbol would tell the user nothing.
- There are no icons, and no column headers, because the name and size columns are clear without them.
- About 80% of the dialog's cells hold data or the decision.

## Smaller terminals

- **60 columns:** the dialog takes the full width minus a 1-column gap on each side. The summary line wraps to two lines, names are cut harder, and sizes stay.
- **Short terminals:** below about 16 rows, the item list shrinks to just the summary line plus `l list items`.
- **Too small:** below about 40×10, the prompt falls back to a single status-line prompt: `Trash 14 marked (1.7 GB)? [y/N]`.
