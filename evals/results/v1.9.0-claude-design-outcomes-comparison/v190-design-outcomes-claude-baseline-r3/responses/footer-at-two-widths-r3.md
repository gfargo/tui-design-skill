## 80 columns (75 used)

```
enter open  / filter  j/k move  r refresh  d delete  y copy  ? help  q quit
```

## 40 columns (36 used)

```
enter open  / filter  ? help  q quit
```

## How I built it

- **Order:** Hints run from most-used to least-used, left to right. `? help` and `q quit` are always the last two.
- **Always shown:** `?` and `q`. Help is how people find every hint that got cut, so it has to stay. Not knowing how to quit is the worst way to get stuck in a TUI, and the hint only costs 6 columns.
- **Fitting:** Each item is `key label`, with two spaces between items so the pairs can't be misread (`j/k move r refresh` with single spaces is hard to parse). I stopped adding hints before reaching the last column, because writing to the last column makes some terminals wrap.

**Dropped at 80:** `e edit` (5%), `s sort` (4%), `t tag` (3%), `: command` (2%). After the first six hints and the two fixed ones, adding `e edit` would take the line to 83 columns. These four are the least-used actions, and `?` lists them.

**Dropped at 40:** `j/k move`, `r refresh`, `d delete`, `y copy` (on top of the four above). At this width there's room for only two hints plus help and quit:
- **`j/k move` (35%):** Most people press the arrow keys first. If your app supports arrows, people can move around without reading the footer, so this hint adds the least of the high-use ones.
- **`r refresh` (20%):** This is the next one by frequency, and adding it would make the line 47 columns. If people use it this much because the listing goes out of date, auto-refreshing would fix that better than a hint.
- **`d delete` (8%) and `y copy` (6%):** These are used less, and `?` covers them. Leaving delete out of the narrow footer also makes it a little harder to hit by accident.
- **Kept `/ filter`:** I kept it over `j/k` even though `/` isn't an obvious key and 40% of users rely on it. Hints are most useful for keys people wouldn't guess.

To make the keys stand out, show them in bold or a different color instead of brackets like `[q]`. That costs no extra columns.
