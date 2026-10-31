I followed the skill's footer rule: most-used action first, `?` always last, and when the line is too long, drop the least-used hints until it fits.

**80 columns** (78 cells):
```
enter open ⋅ / filter ⋅ j/k move ⋅ r refresh ⋅ d delete ⋅ y copy path ⋅ ? help
```

**40 columns** (30 cells):
```
enter open ⋅ / filter ⋅ ? help
```

The separator is `⋅` (U+22C5), which is always one cell wide. Don't use `·` (the middle dot): some terminals draw it two cells wide, which throws off the width math. If you need plain ASCII, use `|`. It's also one cell, so these widths stay the same.

### How the 80-column line was built
With every hint in, the line is 116 cells. I dropped the least-used hints one at a time: `: command` (2%), `t tag` (3%), `s sort` (4%), `e edit` (5%). That brings it to 78 cells, which leaves a little margin at the right edge.

`q quit` is also left out at 80 columns, even though it has no frequency in your logs. Adding it makes the line 87 cells, so something else would have to go. Quit is the most widely known terminal convention, Ctrl+C and Esc also get people out, and the `?` help screen lists it. If your logs show new users getting stuck and unable to exit, swap `q quit` in for `y copy path`. The line is then 73 cells.

### What I dropped at 40 columns, and why
Continuing in the same order:

| Dropped | Usage | Why |
|---|---|---|
| `y copy path` | 6% | Least used of the hints left at 80 |
| `d delete` | 8% | Next least used |
| `r refresh` | 20% | Next least used. The line is still 41 cells |
| `j/k move` | 35% | At 41 cells it misses by one column. It's also the cheapest to lose: arrow keys move the cursor without any hint, so only the vim aliases lose their prompt |

`enter open` (90%) and `/ filter` (40%) stay because they're the two most-used actions. `? help` stays because it's the one key that leads to every hint that got dropped.

**Don't backfill.** After dropping `j/k`, there's room for `e edit` (39 cells), but don't add it. Showing a 5% action while hiding 35% and 20% ones would teach users the wrong things about the app. Drop from the bottom of the list and stop. Don't fill gaps with rare keys.

### Implementation note
Don't hard-code the two strings. Keep one keymap list in priority order (`enter, /, j/k, r, d, y, e, s, t, :`), with `?` attached at the end. On every resize, measure each hint in terminal cells, not string length, and drop from the end until the line fits. Then pin both widths in snapshot tests, along with a 60-column tmux split. At 60 columns this method gives `enter open ⋅ / filter ⋅ j/k move ⋅ r refresh ⋅ d delete ⋅ ? help` (59 cells), which only just fits.
