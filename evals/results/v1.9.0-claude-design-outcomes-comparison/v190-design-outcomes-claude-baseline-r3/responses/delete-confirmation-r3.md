Here's my design. I assumed a full 80×24 screen with the confirmation drawn over the file list.

```
 ~/photos/2026                                           3,000 items · 14 marked
   IMG_0397.jpg
  ┌─ Delete 14 marked items ─────────────────────────────────────────────────┐
  │                                                                          │
  │  Move to Trash: 12 files and 2 folders (318 files inside)        1.4 GB  │
  │  12 of these are not visible on screen right now.                        │
  │                                                                          │
  │    raw/  (212 files)                                1.1 GB   2026-09-02  │
  │    exports/  (106 files)                            212 MB   2026-09-20  │
  │    contact-sheet.pdf                               18.2 MB   2026-09-21  │
  │    IMG_0412.jpg                                     4.1 MB   2026-09-14  │
  │    IMG_0413.jpg                                     3.9 MB   2026-09-14  │
  │    IMG_0419.jpg                                     4.4 MB   2026-09-14  │
  │    IMG_0502.jpg                                     4.0 MB   2026-09-17  │
  │    IMG_0503.jpg                                     3.8 MB   2026-09-17  │
  │    … 6 more (↑/↓ to scroll)                                              │
  │                                                                          │
  │  Not included: notes.txt (under the cursor, but not marked).             │
  │                                                                          │
  │  y  Move to Trash      n / Esc  Cancel      D  Delete permanently…       │
  └──────────────────────────────────────────────────────────────────────────┘
   IMG_0431.jpg
   IMG_0432.jpg
 -- confirm delete --
```

**Why it looks like this**

- **It lists what will be deleted.** The 14 marks are spread across 3,000 rows, and most of them are off-screen. Line 3 says so outright, so the user can check them before saying yes.
- **Folders come first and show their contents.** "14 items" sounds small, but two of them are folders holding 318 files. That's the number most likely to surprise someone.
- **It says what's left out.** People often get confused about whether `d` acts on the marked files or on the file under the cursor. The dialog names the cursor file and says it won't be deleted.
- **The default action can be undone.** `y` moves files to the Trash. Permanent deletion takes a separate, deliberate step.

**Keys**

| Key | Action |
|---|---|
| `y` | Move all 14 items to the Trash and close the dialog. The marks are cleared and the cursor moves to the next remaining file. The status line shows `Moved 14 items to Trash · u to undo`. |
| `n`, `Esc` | Cancel. Nothing changes and **all 14 marks stay**, so the user can adjust them and press `d` again. |
| `↑` `↓` `PgUp` `PgDn` | Scroll the item list inside the dialog. |
| `D` | Switch to permanent deletion (see below). |
| `Enter` | **Does nothing.** It flashes the hint line instead. Enter gets typed by habit or by key-ahead, so it shouldn't confirm anything that deletes files. |
| `d` | **Does nothing.** Vim users press `dd` by reflex, and the second `d` must not confirm. |
| anything else | Ignored. The dialog stays open. |

Also, ignore all keys for about 150 ms after the dialog opens. That keeps key-repeat or a fast double-tap from answering it.

**After `D`**, the bottom of the dialog changes and the border/title turn red:

```
  │  ⚠ Permanently delete 14 items and 318 files inside (1.4 GB)?            │
  │    This cannot be undone.                                                │
  │                                                                          │
  │  y  Delete forever      n / Esc  Back to Trash option                    │
  └──────────────────────────────────────────────────────────────────────────┘
```

In this state, `y` deletes permanently, and `n`/`Esc` go back to the first dialog without cancelling everything.

**Edge cases**

- **Nothing marked:** the dialog acts on the cursor file and names it ("Move notes.txt to Trash?"). It skips the list and the "not included" line.
- **No Trash available** (network drive, another filesystem): the dialog opens straight into the red permanent state, with a line saying why: "Trash isn't available on this drive."
- **Hundreds of marks:** the layout stays the same and the list just scrolls. The summary line with counts and size matters most at that point.
