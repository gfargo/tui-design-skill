Give it the conventional scrolling keys and a right-aligned `current/total` count. A scrollbar is optional.

## Keys

| Keys | Moves |
|---|---|
| `↑`/`↓`, `k`/`j` | One row |
| `PgUp` / `PgDn` | One page, keeping one row from the previous page visible |
| `Ctrl+U` / `Ctrl+D` | Half a page |
| `Home` / `End`, `g` (or `gg`) / `G` | Top / bottom |
| Mouse wheel | Scrolls the list under the pointer. It doesn't move the selection. |

How they should behave:
- **Keep a margin around the cursor.** As the selection moves, keep it at least 3 rows from the top or bottom edge of the list, so the user can see what's coming. If the list area is under 12 rows tall, drop that to 1 row.
- **Bind both arrows and `hjkl`.** Turn off the letter keys and `Ctrl+U` while a text field such as a `/` filter prompt has focus. In a text field, `Ctrl+U` means "delete line."
- **Choose `g` or `gg` for "top" and use it everywhere.** Use `gg` if you might later want `g` as the first key of other two-key commands.
- **Every key needs a non-Ctrl path.** Paging already has `PgUp`/`PgDn`, so a `Ctrl+D` that tmux or Zellij intercepts won't leave anyone stuck.

## Position indicator

Right-align `selected/total` in the list's title or footer, with thousands separators:

```
┌ Items ─────────────────────────────────── 42/1,203 ┐
│   item-0040                                         │
│ ▸ item-0042                                         │
│   item-0043                                         │
└─────────────────────────────────────────────────────┘
 ↑↓/jk move  PgUp/PgDn page  g/G top/end  / filter  ? help
```

- **Lists show a count. Documents and logs show a percentage.**
- **When a filter is active, count the matches:** `3/45 · 1,203 total`. The number the user needs is "where am I among what I can see."
- **A scrollbar is optional decoration.** The count carries the meaning, takes no width and is read by screen readers. A scrollbar takes a column, which matters in a 60-column tmux split.
- **At narrow widths, the count stays.** At 60 columns, drop the title text before the count, then shorten the footer hints to `? help`.

## If the list updates live

Track the selection by a stable ID, not by row index. When rows are added or removed above the cursor, keep the selected row in the same place on screen. If the list streams new items, add follow mode: scrolling up pauses it, `G` or `F` resumes it, and a `▾ N new` badge shows what arrived while paused.

If you tell me the framework (Bubble Tea, Ratatui, Textual, Ink…), I can show how to wire these keys and derive the footer hints from the keymap.
