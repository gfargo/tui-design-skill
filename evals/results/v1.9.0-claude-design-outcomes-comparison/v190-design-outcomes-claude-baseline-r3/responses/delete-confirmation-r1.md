Assumptions: the terminal is 80×24, the 14 marked files are scattered through a 3,000-file directory, and the cursor is on a file that isn't marked.

```
 ~/projects/archive                                      3,000 items · 14 marked
 ───────────────────────────────────────────────────────────────────────────────
   notes.md
    ┌─ Move 14 marked items to Trash? ─────────────────────────────────────┐
    │  14 items · 2 folders containing 318 files · 41.2 MB total           │
    │  11 of the 14 are outside the visible part of the list.              │
    │                                                                      │
    │  ▸ 2023-q1-report.pdf                  row 41                2.1 MB  │
    │    2023-q2-report.pdf                  row 42                2.3 MB  │
    │    build/  (204 files)                 row 388              18.0 MB  │
    │    cache.sqlite                        row 391               6.4 MB  │
    │    dist/  (114 files)                  row 870               9.8 MB  │
    │    draft-v1.docx                       row 1,204             412 KB  │
    │    draft-v2.docx                       row 1,205             430 KB  │
    │    IMG_2201.HEIC                       row 2,977             3.1 MB  │
    │    … 6 more  (j/k to scroll)                                         │
    │                                                                      │
    │  Not included: notes.md (under the cursor, but not marked).          │
    ├──────────────────────────────────────────────────────────────────────┤
    │  y  Move 14 to Trash    u  Unmark ▸ item    n/Esc  Cancel            │
    └──────────────────────────────────────────────────────────────────────┘
   photo-0392.jpg
 d: delete marked · confirm with y
```

## Keys

| Key | Action |
|---|---|
| `y` | Moves all items still listed to Trash, closes the dialog and clears the marks. Shows "Moved 14 items to Trash · z to undo" in the status line. |
| `n`, `Esc`, `q` | Cancels. Nothing is deleted and the marks stay. |
| `Enter` | Does nothing except flash "press y to confirm". People press Enter by reflex, so it shouldn't trigger a destructive action. |
| `j`/`k`, `↓`/`↑` | Moves the `▸` highlight through the list, scrolling to show the 6 hidden items. |
| `PgDn`/`PgUp` | Scrolls the list a page at a time. |
| `u` | Unmarks the highlighted item and removes it from the batch. The title and counts update right away (for example, "Move 13 marked items…"). If you unmark the last item, the dialog closes. |
| Anything else | Ignored. The dialog stays open so a stray key can't confirm or dismiss it. |

## Why it looks like this

- **The scope is stated in the title.** "14 marked items" makes it clear that `d` acts on the marks and not on the file under the cursor. The "Not included: notes.md" line answers the obvious question: "wait, which file did it think I meant?"
- **It warns about files you can't see.** With 3,000 files, most marks were made several screens ago. "11 of the 14 are outside the visible part" tells you you're about to delete things you haven't looked at recently. The row numbers show where each one is.
- **It counts what's inside folders.** "14 items" sounds small, but here it's really 332 files. Showing the folder contents and the total size prevents that surprise.
- **You can fix the batch without starting over.** With `u` you can drop one wrong item without cancelling, finding it among 3,000 rows, unmarking it and pressing `d` again.
- **The default action is reversible.** Files go to Trash and can be restored with `z`. Permanent deletion isn't offered in this dialog.

## Variants

- **No Trash available** (network or removable volume): the title changes to `Permanently delete 14 items?`, the box border turns red, and `y` is replaced by typing `delete` and pressing Enter. Accidental keypresses can't do irreversible damage.
- **Only one item marked:** the list collapses to that single file name, and the "outside the view" line appears only if that file is off-screen.
