## 80 columns

```
enter open  / filter  j/k move  r refresh  d delete  y copy  ? help  q quit
```

This line is 75 columns wide. I kept it under 80 because some terminals wrap or scroll when text reaches the last column.

## 40 columns

```
enter open  / filter  ? help  q quit
```

This line is 36 columns wide.

## How the hints are chosen

1. **`? help` and `q quit` always stay, even though they have no usage numbers.** `?` is how users find every hint that got dropped, so it makes dropping the others safe. `q` is the way out, and a new user who can't see how to quit is stuck. Both sit at the end of the line.
2. **The other hints are added in order of how often they're used:** enter, /, j/k, r, d, y, e, s, t, :. Each hint costs its own width plus a 2-space gap. When the next hint doesn't fit, stop adding.
3. **Hints are dropped whole.** Never cut a label short. A partly cut hint like `r ref` is worse than none.

## Dropped at 40 columns

| Hint | Usage | Why it was dropped |
|---|---|---|
| `j/k move` | 35% | It's the next hint in usage order and would take the line to 46 columns. Arrow keys also work for moving, so users who don't know j/k can still move around. |
| `r refresh` | 20% | Too wide (it would reach 47 columns). It's also less used than everything kept. |
| `d delete`, `y copy` | 8%, 6% | Less used and too wide. Help still lists them. |

At 80 columns, `e edit` (5%), `s sort` (4%), `t tag` (3%) and `: command` (2%) are already dropped. Adding `e edit` would push the line to 83 columns. Together those four make up under 15% of usage, and users who need them find them through `?`.

I shortened `y copy path` to `y copy` so it fits at 80 columns. With the full label the line would be exactly 80 columns, which is the edge case mentioned above.

When the terminal is resized, run the same steps again instead of switching between two fixed strings. That way every width in between, like 60 columns, also gets the best line that fits.
