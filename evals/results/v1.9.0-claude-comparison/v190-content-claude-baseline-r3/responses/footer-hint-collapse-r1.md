Your working directory is empty, so I designed this from scratch. I assumed these eight actions: open, copy, move, rename, delete, new folder, find and quit, plus `?` for help.

## Design rules

1. **Keys are bold in the accent color and labels are dim.** Don't use brackets like `[c]` or `<c>`. They take up columns and add clutter. The color difference is enough to tell keys from labels.
2. **Put 2 spaces between items and 1 space between a key and its label.** That makes each key clearly belong to its own label.
3. **Pin `? help` and `q quit` to the right edge.** They're at every width, always in the same spot, so users learn where to look.
4. **When space runs out, drop whole items in priority order.** Never shorten labels to things like `ren` or `del`, because people can't read them at a glance.
5. **When items are hidden, `? help` becomes `? more`.** That tells the user the bar is incomplete and where to find the rest.
6. **Make delete `D` (Shift+d).** It's the one destructive action, so a lowercase `d` hit by accident shouldn't trigger it.

**Priority order** (dropped from the end first): open, copy, move, find, rename, new folder, delete. Help and quit are never dropped.

## 80 columns

```
         1         2         3         4         5         6         7         8
12345678901234567890123456789012345678901234567890123456789012345678901234567890
┌──────────────────────────────────────────────────────────────────────────────┐
│ ~/projects/tui-fm                                            12 items  4.2 MB│
│ …                                                                            │
├──────────────────────────────────────────────────────────────────────────────┤
 ⏎ open  c copy  m move  r rename  D delete  n mkdir  / find     ? help  q quit 
```

All eight actions fit. The bar is exactly 80 columns: 60 for the action group, a gap of 5 or more, 14 for the help/quit pair, and 1 space of right padding. The gap is what separates the two groups visually, so it should stay at least 3 wide. If it would be smaller, drop the next item instead.

## 40 columns

```
         1         2         3         4
1234567890123456789012345678901234567890
┌──────────────────────────────────────┐
│ ~/projects/tui-fm          12 items  │
│ …                                    │
├──────────────────────────────────────┤
 ⏎ open  c copy  m move  ? more  q quit 
```

The three most-used actions stay visible. Pressing `?` opens an overlay with all the keys:

```
┌─ Keys ───────────────────────────────┐
│  ⏎  open          r  rename          │
│  c  copy          D  delete          │
│  m  move          n  new folder      │
│  /  find          q  quit            │
│                                      │
│              esc close               │
└──────────────────────────────────────┘
```

The two-column grid needs 36 columns, so it fits at 40. Below that, switch it to a single column.

## Narrower and context-dependent states

- **Under about 26 columns:** show only `? more  q quit`.
- **Files selected:** replace `⏎ open` with a count, e.g. `3 sel  c copy  m move  D delete …`. Open doesn't apply to several files, and the count confirms what the next action will affect.
- **Prompt modes (rename, find, delete confirmation):** replace the whole bar with that mode's keys, e.g. `⏎ confirm  esc cancel`. Two keys are easy to read, and it makes the mode change obvious.

## Implementation notes

- I counted `⏎` as 1 column. It's 1 column in almost every terminal, but measure it with `wcwidth` and fall back to `enter` if the measured width isn't 1. `enter` is 4 columns wider, so at 80 columns the gap shrinks to 1 and, by the rule above, `/ find` is dropped.
- Don't fit items by counting characters. Build the bar by adding items in priority order until the next one wouldn't fit while leaving the right group, a gap of at least 3, and 1 space of padding. Then switch `help` to `more` if any item was skipped.
- Don't draw anything in the last column of the last row. Some terminals scroll when that cell is written, which is why the bar ends with a space.

If you tell me which TUI library you're using (Bubble Tea, Ratatui, Textual, etc.), I can write the fitting function and styles for it.
