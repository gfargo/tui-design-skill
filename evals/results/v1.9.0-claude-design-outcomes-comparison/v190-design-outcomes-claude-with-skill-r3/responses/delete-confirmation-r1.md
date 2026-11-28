When the user presses `d` with 14 items marked, the app should **move those 14 to the Trash** after a simple yes/no prompt that defaults to No. The prompt must **list the items**, because 11 of the 14 are not visible on screen. It acts on the marked items only. It does not act on the cursor row.

### The sketch (80×24)

```
 ~/projects/atlas                                       3,000 items · 14 marked
   api/                                                            -  2026-09-30
>  assets/                                                         -  2026-10-22
 * build-c┌─ Confirm delete ─────────────────────────────────────────┐2026-10-11
   cmd/   │                                                          │2026-08-14
   docs/  │  Move 14 marked items to Trash? [y/N]                    │2026-10-20
 * legacy/│  12 files and 2 folders (306 files inside), 1.7 GB       │2026-03-02
   lib/   │  11 are not in the current view. Review the list:        │2026-10-25
   node_mo│                                                          │2026-10-26
   scripts│    legacy/                        301 files    1.2 GB    │2026-09-09
   test/  │    build-cache/                     5 files    410 MB    │2026-10-27
   .editor│    render-final.mov                           38.2 MB    │2026-01-15
   .env.ex│    archive/2023.tar.gz                        21.6 MB    │2026-07-30
   .gitign│    notes-2024-01.md                            4.1 KB    │2026-05-18
   CHANGEL│    ↓ 9 more                                              │2026-10-02
   LICENSE│                                                          │2025-12-01
   Makefil└──────────────────────────────────────────────────────────┘2026-10-01
   README.md                                                  6.1 KB  2026-10-27
   go.mod                                                     0.4 KB  2026-10-19
   go.sum                                                    48.0 KB  2026-10-19
   main.go                                                    3.4 KB  2026-10-27
 * notes-2024-01.md                                           4.1 KB  2024-01-31
   package.json                                               1.9 KB  2026-10-24
 CONFIRM DELETE   y move to Trash   n/Esc/Enter cancel   j/k scroll list
```

### What each key does

| Key | Effect |
|---|---|
| `y` | Moves all 14 marked items to the Trash, closes the dialog and clears the marks. The status bar then shows `Moved 14 items to Trash · u undo`. |
| `n`, `Esc`, `Enter` | Cancels. **Enter means No**, as the capital `N` in `[y/N]` shows. The marks stay, so the user can unmark one item and press `d` again. |
| `Ctrl+C` | Cancels the dialog. It does not quit the app. |
| `j`/`k`, `↓`/`↑`, `PgDn`/`PgUp` | Scroll the list of marked items. This list is the only place the 11 off-screen items can be seen. |
| Any other key, **including `d`** | Ignored. A fast double `dd` must not confirm, and keys typed in the dialog must not reach the file list behind it. |

### Why it looks like this

- **The prompt tells the user what is about to happen.** The title shows the count, `[y/N]` shows the default and the summary shows the total size. The line about items "not in the current view" warns the user that they can't see most of what they're deleting.
- **Folders come first, then everything else by size.** The 301 files inside `legacy/` are the biggest risk, so they're at the top. Paths are relative to the current folder, which makes marks in other folders, like `archive/2023.tar.gz`, easy to spot.
- **The cursor isn't on a marked row.** The cursor is on `assets/`, which is not marked. Marked items always take priority, and the prompt names only them, so it's clear that `assets/` isn't included.
- **A simple yes/no is enough here.** Moving to the Trash can be undone, so the light confirmation level fits. If the Trash isn't available (a network mount, or `Shift+D` for permanent delete), use the same dialog with the title `Permanently delete` and the line `This cannot be undone.` Don't put a "delete permanently" option inside this dialog, where it would be one key away from `y`.
- **The work shouldn't freeze the app, and failures should be reported honestly.** Moving 306 files to the Trash can take a moment. Do it in the background and show progress in the status bar. If some items fail, say so, for example `Moved 13 of 14 · 1 failed: permission denied`, and leave the failed item marked so the user can retry.

### Clutter audit
- **Borders:** only one, the dialog's own border.
- **Marked rows:** shown by a `*` plus an accent background (two signals), and only on marked rows.
- **Dialog rows:** no per-row icons. Folders are shown by the trailing `/` and the file count.
- **Key hints:** only in the footer, which changes to `CONFIRM DELETE` so the user knows a dialog is open even without color. The only hint repeated inside the dialog is `[y/N]`.

### At 60 columns
The dialog grows to 56 columns, nearly the full width. The file-count column is dropped and the size stays. The summary wraps onto two lines, and the list shows 4 rows plus `↓ 10 more`. Below about 40×12, use the status line instead of a dialog: `Trash 14 marked (1.7 GB)? [y/N]`.
