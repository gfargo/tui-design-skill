I've read the skill's footer and responsive guidance, so here's the design.

## Footer hint bar

The footer is one line: `key action ⋅ key action`, ordered from most to least used, with `? help` always last. When the line doesn't fit, hints are dropped from the right end of the list, but `? help` is never dropped. Because of that, nothing is ever more than one key away, and the eight actions don't need to be squeezed onto one line.

**Priority order (assumed; reorder to match your app):**
`enter open` → `/ filter` → `space select` → `c copy` → `m move` → `d delete` → `r rename` → `n new` → `q quit` → `? help` (always shown)

**80 columns** (75 cells used):
```
 enter open ⋅ / filter ⋅ space select ⋅ c copy ⋅ m move ⋅ d delete ⋅ ? help
```

**40 columns** (31 cells used):
```
 enter open ⋅ / filter ⋅ ? help
```

**60 columns** (54 cells used). I added this one because a 60-column tmux split is the narrow width people actually use:
```
 enter open ⋅ / filter ⋅ space select ⋅ c copy ⋅ ? help
```

All eight actions together take 102 cells, so they never fit on one line. `r rename`, `n new` and `q quit` only appear in the `?` help. They are the least-used actions, or in quit's case a convention people already know.

## Change the hints by context

The footer is most useful when it reflects what the user is doing. With files selected, the most likely next actions change:

```
80:  3 selected ⋅ c copy ⋅ m move ⋅ d delete ⋅ esc clear ⋅ ? help
40:  3 selected ⋅ c copy ⋅ m move ⋅ ? help
```

While the filter is being typed, letter keys go to the text field, so the hints must not list them:
```
 enter keep ⋅ esc cancel
```

## Styling (clutter check)

- **Key:** bold or the accent color. **Action:** default text. **Separator:** dim. A key needs only that one signal. Don't add `<enter>` or `[c]` brackets, since they repeat what the bold already shows.
- Use `⋅` (U+22C5) as the separator, not `·`, which has ambiguous width and can break alignment in some terminals. The ASCII fallback is `|`.
- Under `NO_COLOR`, bold alone is enough to set keys apart from actions.
- Don't show arrow or `hjkl` navigation hints. They take up space without telling anyone something new.

## Implementation notes

- Define each binding once with a priority. Build the footer from that keymap and generate the `?` help screen from the same list, so the two can't drift apart.
- Fitting: always place `? help`. Then add hints in priority order while `width(line) + width(hint) + 3 ≤ cols − 1`. Measure with a cell-width function, not string length.
- Rebuild the footer on every resize event. Add golden tests at 80, 60 and 40 columns, plus one with labels made about 50% longer to simulate translations.
- About 40 columns: that line only matters if your single-pane layout really works at that width. If your minimum is 60, the "terminal too small (need 60 cols)" message should replace the whole screen, including the footer.
