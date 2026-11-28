## 80 columns

```
 enter open ⋅ / filter ⋅ j/k move ⋅ r refresh ⋅ d delete ⋅ y copy path ⋅ ? help 
```

The hints take 78 cells, with one column of padding on each side. I ordered them by how often your logs say they're used, and put `?` last.

## 40 columns

```
 enter open ⋅ / filter ⋅ ? help
```

That's 30 cells.

## What I dropped and why

The rule I used: show hints in order of use, drop the least-used from the right until the line fits, and always keep `? help` so the full list is one key away.

**Dropped at 40 columns:**

- **`j/k move` (35%)**: This is the hardest cut because it's used a lot. Adding it makes the line 41 cells, which is over 40, and there's no room for padding. Cutting it costs little because movement is easy to discover: users press the arrow keys or j/k and see the cursor move. Enter, filtering and help aren't discoverable that way.
- **`r refresh` (20%), `d delete` (8%), `y copy path` (6%)**: These are used less than everything that stayed, so they go first.

**Dropped at both widths:**

- **`e edit` (5%), `s sort` (4%), `t tag` (3%), `: command` (2%)**: At 80 columns, adding `e edit` would make the line 87 cells. These were the least-used keys that didn't fit, so `?` covers them.
- **`q quit`**: You didn't give a frequency for it, so this is a judgment call. People quit once per session, they learn the key once, and `q` (plus `Ctrl+C`) is a standard terminal convention. Showing it at 80 columns would push out `y copy path`, which your logs do show being used. If you'd rather keep quit visible for first-time users, use `… ⋅ d delete ⋅ q quit ⋅ ? help` (73 cells).

## Format details

- **Separator:** I used `⋅` (U+22C5) with a space on each side. Don't use the middle dot `·`: some terminals draw it two cells wide, which would break the width math.
- **Enter key:** It's written as `enter` rather than `↵` because `↵` also has an unreliable width.
- **Fitting the line:** Generate the line from your keymap in priority order and measure terminal cell width, not string length. That way any width between 40 and 80 gets the longest prefix that fits, plus `? help`, and you don't need two hand-written strings.
- **Context:** The footer should change with context. While the `/` filter is being typed, it should read `enter accept ⋅ esc cancel` instead.
