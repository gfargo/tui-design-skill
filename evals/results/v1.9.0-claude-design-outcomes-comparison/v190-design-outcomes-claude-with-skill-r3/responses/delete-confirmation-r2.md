With 3,000 rows on screen, most of the 14 marks are probably scrolled out of view, so the user can't actually see what `d` will act on. The confirmation should list every marked item, sizes included, before it asks.

**Recommendation:** `d` moves the items to the Trash and asks one `[y/N]` question with No as the default. A typed confirmation is too much for a delete that can be undone.

### 80×24 sketch

```
 ~/projects/site                                        3,000 items · 14 marked
   app-2026-09-27.log                                                    84 MB
        ┌─ Delete 14 items ────────────────────────────────────────────┐
        │                                                              │
        │ 14 marked items · 12 files, 2 folders · 1.4 GB               │
        │ The 2 folders contain 318 more files.                        │
        │                                                              │
        │   build/  (311 files)                                 1.2 GB │
        │   node_cache/  (7 files)                               41 MB │
        │   app-2026-10-01.log                                   88 MB │
        │   app-2026-10-02.log                                   86 MB │
        │   core.dump                                            12 MB │
        │   screenshot 2026-09-14.png                           1.9 MB │
        │   draft-old.md                                          4 KB │
        │   notes (copy).txt                                      2 KB │
        │   ▾ 6 more below · j/k to scroll                             │
        │                                                              │
        │ Goes to the Trash. Press u right after to undo.              │
        │ Move 14 items to the Trash?  [y/N]                           │
        │                                                              │
        └──────────────────────────────────────────────────────────────┘
   app-2026-10-03.log                                                    85 MB
   app-2026-10-04.log                                                    83 MB
 CONFIRM   y move to Trash   n/Esc/Enter cancel   j/k scroll list
```

The file list behind the dialog is dimmed, and the cells under the dialog are cleared. The border, the title and the `CONFIRM` footer show that a dialog is open even without color or the faint attribute.

### Keys

| Key | Effect |
|---|---|
| `y` / `Y` | Moves all 14 items to the Trash, closes the dialog and clears the marks. The cursor stays at the same position on the next remaining row. The status line shows `Moved 14 items to Trash · u undo`. |
| `n`, `Esc`, `Enter` | Cancels. **The 14 marks stay**, so the user can review them and press `d` again. `Enter` cancels because No is the default (that's what the capital `N` means). |
| `Ctrl+C` | Cancels the dialog like `Esc` does. It doesn't quit the app from inside the dialog. |
| `j`/`k`, `↓`/`↑`, `PgDn`/`PgUp` | Scrolls the list of marked items. The `▾ 6 more` line counts down as you scroll. |
| Any other key, **including a second `d`** | Does nothing. Someone used to vim's `dd` shouldn't be able to confirm by accident, and keys don't pass through to the list behind. |
| `u` (after closing) | Restores the 14 items from the Trash to where they were. |

### Rules behind the design
- **The dialog acts on the marks, not the cursor.** If the cursor is on an unmarked file, that file is left alone. The list shows exactly what will be deleted.
- **It counts what's inside folders.** "14 items" sounds small, but here it includes 318 more files. Show that next to the total size.
- **It includes hidden marks.** If a filter is hiding some marked files, add a line such as `3 of these are hidden by the filter "*.log"` and keep them in the list.
- **It never deletes permanently without saying so.** If the Trash isn't available (a network mount, or no Trash on the system), change the dialog to `Permanently delete 14 items? This cannot be undone. [y/N]`. Don't fall back to permanent deletion silently. A separate `D` key for permanent delete uses that same wording. It stays `y/N` with No as the default: 14 files the user chose themselves don't call for typing a name.

### Clutter audit
- There's one border, with no second box around the file list.
- The default is shown once, by the capital `N`.
- Key hints appear only in the footer, which replaces the normal hints while the dialog is open. They aren't repeated inside the dialog.
- No markers appear on every row. Folders are marked with a trailing `/` and their file count.

### At 60 columns
The dialog shrinks to 56 columns. The size column keeps its width, and long names are shortened in the middle (`screenshot 20…09-14.png`). The list shows fewer rows, and the `▾ N more` count goes up to match.
