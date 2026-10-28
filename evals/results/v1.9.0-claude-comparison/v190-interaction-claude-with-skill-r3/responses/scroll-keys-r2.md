**Short answer:** Use the standard scrolling keys and show a `42/1,203` count, right-aligned in the panel title or footer. A scrollbar is optional.

## Keys

| Keys | Moves |
|---|---|
| `↑`/`↓` and `k`/`j` | One row |
| `PgUp`/`PgDn` | One page, keeping one row of overlap so the user doesn't lose their place |
| `Ctrl+U`/`Ctrl+D` | Half a page |
| `Home`/`End` and `g`/`G` | Top / bottom |
| Mouse wheel | Scrolls the viewport under the pointer. It doesn't move the selection. |

Some notes:
- **`g` or `gg`:** Use `gg` if `g` already starts other two-key commands (vim style). Otherwise a single `g` is fine. Either way, keep `Home`/`End` so people who don't use vim have a way to the top and bottom.
- **`hjkl` only when nothing is being typed.** While a filter box or other text field has focus, `j`, `k`, `g` and `G` are just letters. The arrow keys and PgUp/PgDn have to keep working then.
- **Don't build anything on `Ctrl+B`/`Ctrl+F`.** tmux uses `Ctrl+B` as its prefix, so make sure every scroll action has another key.
- **Keep a scroll margin.** Hold the cursor at least 3 rows from the top or bottom edge while it moves, so the user sees the next rows before reaching them. In viewports under 12 rows tall, use 1 row.

## Position indicator

Show `selected/total`, e.g. `42/1,203`, right-aligned. For documents, a percentage works better than a row count.

- **The count does the job; a scrollbar is decoration.** The count costs no width, makes sense in monochrome, and screen readers can read it. Add a scrollbar only if you want it, and never instead of the count.
- **When filtering, show matches and total**, e.g. `12/45,678` or `3/12 (45,678)`, so the user can see that the list is filtered.
- **Show one indicator, in one place.** Showing the same position as a count, a scrollbar *and* a percentage gives three signals for one fact, which is clutter.

```
Wide (120 cols)
┌ Items ─────────────────────────────────────────────── 42/1,203 ┐
│   …                                                            │
│ ▌ selected row                                                 │
│   …                                                            │
└────────────────────────────────────────────────────────────────┘
 j/k move  ^d/^u half page  g/G top/bottom  / filter  ? help

60-column split
Items                                          42/1,203
 ▌ selected row
   …
 j/k move  g/G ends  / filter  ? help
```

At 60 columns, drop the border and keep the count. The count is the last piece of chrome to cut, because it's the only thing telling the user where they are.

## If the list refreshes live

Track the selected row by a stable ID, not its row number. When rows are added or removed above the selection, keep the selected row in the same place on screen, and don't re-sort on refresh. If the selected item disappears, move to its nearest neighbour, not back to the top.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink…), I can show how to wire these keys and the count into its list or viewport widget.
