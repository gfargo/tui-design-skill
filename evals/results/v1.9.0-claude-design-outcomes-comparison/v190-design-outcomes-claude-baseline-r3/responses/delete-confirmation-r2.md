## The confirmation

The list has 3,000 rows and the 14 marks are probably spread across screens the user hasn't looked at for a while. So the dialog lists what will be deleted, by name. A count alone isn't enough.

```
 ~/projects/photos                                       3,000 items · 14 marked
┌─ Delete 14 marked items? ────────────────────────────────────────────────────┐
│                                                                              │
│  Move to Trash: 12 files + 2 folders containing 318 more · 2.2 GB total      │
│                                                                              │
│  ▸ raw/                                       folder · 301 files · 2.1 GB    │
│    old-exports/                               folder ·  17 files ·  88 MB    │
│    DSC_1180.NEF                                                   24.8 MB    │
│    IMG_0412.jpg                                                    4.2 MB    │
│    IMG_0413.jpg                                                    3.9 MB    │
│    Thumbs.db                                                       1.1 KB    │
│    ↓ 8 more — scroll to review all 14                                        │
│                                                                              │
│  Cursor is on notes.txt, which is not marked and will be kept.               │
│                                                                              │
│  y move to Trash    n / Esc cancel    x unmark    ↑↓ PgUp PgDn scroll        │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Keys

| Key | Action |
|---|---|
| `y` | Moves all items still in the list to the Trash and closes the dialog. This is the only key that deletes. |
| `n`, `Esc`, `q` | Cancels. Nothing is deleted and all 14 marks stay. |
| `x` / `Space` | Unmarks the highlighted (`▸`) item. It leaves this batch and loses its mark in the main list too. The title and summary update ("Delete 13 marked items?"). Unmarking the last item closes the dialog. |
| `↑` `↓` / `j` `k` | Moves the highlight. |
| `PgUp` `PgDn` / `g` `G` | Scrolls through the list when it's longer than the window. |
| `Enter` | Does nothing, on purpose. Pressing `d` then `Enter` is a reflex, and it shouldn't be able to delete 2 GB. |

## Design choices

- **The title says what `d` acts on.** When there are marks, `d` deletes the marks, not the file under the cursor. The title says "14 marked items." If the cursor is on an unmarked file, a line says that file will be kept. This prevents the most common surprise in this situation.
- **The summary includes what's inside folders.** "12 files + 2 folders containing 318 more" shows the real scope. Without it, "14 items" hides 332 files.
- **Folders come first, then everything else by size, largest first.** The riskiest items are at the top, where they'll be seen even if the user doesn't scroll. The 8 hidden items are the smallest ones.
- **The default is the Trash.** The verb "Move to Trash" is in the summary line, so the user knows it can be undone.
- **The dialog can be fixed in place.** `x` lets the user drop one wrong mark without cancelling, fixing it in the list, and pressing `d` again.

## When the Trash isn't available

On a network share or another drive without a Trash, the dialog changes in three ways:

- The title becomes **"Permanently delete 14 items?"**
- The summary line is replaced, in red, with **"No Trash on this drive. This cannot be undone."**
- The confirm key changes from `y` to `D` (Shift-d), and the key line reads `D delete forever`. Because the key is different, pressing `d` then `y` from habit can't permanently delete anything.
