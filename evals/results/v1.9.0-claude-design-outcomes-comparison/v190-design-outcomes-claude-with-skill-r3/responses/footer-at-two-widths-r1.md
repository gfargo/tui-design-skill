I applied the skill's footer rule: the most-used action goes first and `? help` goes last. When the line doesn't fit, drop hints starting from the least-used end until it does. Widths count terminal cells, and each ` ⋅ ` separator is 3 cells.

**80 columns (78 cells):**
```
enter open ⋅ / filter ⋅ j/k move ⋅ r refresh ⋅ d delete ⋅ y copy path ⋅ ? help
```

**40 columns (30 cells):**
```
enter open ⋅ / filter ⋅ ? help
```

**Dropped at 40 columns:**
- **`j/k move` (35%)** is the next hint in line, and adding it makes the line 41 cells, which is too wide. Losing it costs little: people try arrow keys without being told, and `?` still lists j/k.
- **`r` refresh, `d` delete, `y` copy path:** these were already less frequent than `j/k`. `r` alone would also make the line 42 cells.
- **`t tag`, `e edit`, `s sort`:** each of these would technically fit in the 10 spare cells. I left them out on purpose. Putting a 3–5% action in the footer while hiding a 35% one inverts the priority. It would also make the footer look different at every width instead of just getting shorter from the right. The leftover space stays empty.

**Dropped at both widths:**
- **`e` edit, `s` sort, `t` tag, `:` command:** at 80 columns the line holds hints only down to `y` (6%). Adding `e edit` makes it 87 cells.
- **`q` quit:** you didn't give it a frequency, so it ranks below everything that has one. Quitting is still easy to find: `q` is the standard quit key, `Ctrl+C` should also quit, and the `?` screen lists both. `?` is the one hint that is always shown, because it leads to everything else.

**Implementation notes:**
- Build the line from your keymap in priority order, adding hints until the next one won't fit. Don't hard-code a separate string for each width. Measure in terminal cells, not string length.
- Use `⋅` (U+22C5) as the separator, not `·`. Some terminals draw `·` two cells wide, which breaks the width count.
