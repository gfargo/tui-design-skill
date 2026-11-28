## Why it feels busy

1. **Three nested borders.** Going in from the terminal edge to the `api` row, you cross the outer frame, then the panel box, then the inner box. One border at most is enough. Right now 441 of the 534 visible characters (83%) are border lines. Only about 29 characters are real data: three job names, three status words, and one duration.
2. **Each status is shown four ways.** A passing row has `[PASS]`, `ok`, `v`, and green. Each of those says the same thing. The detail pane repeats it a fifth and sixth time with `PASSED (v)`.
3. **Every row has a `>` marker, so it marks nothing.** It also hides a real bug: the detail pane shows `api`, but nothing in the list tells you which row is selected.
4. **Every row is in color.** When all the rows are colored, the red FAIL row doesn't stand out.

## Exactly what to remove

| Remove | Why |
|---|---|
| The outer frame around the whole screen | The terminal edge already frames the app |
| The inner box in both panels | It sits inside another box and separates nothing |
| Both panel boxes. Keep one vertical `\|` between the panes | A single line is enough to separate two panes |
| The `[` `]` brackets | The word `PASS` or `FAIL` is enough on its own |
| The `ok` / `fail` column | It repeats the status word |
| The `v` / `x` column | It repeats the status word a third time |
| The `>` on every row | It's on every row, so it carries no information. Use reverse video on the selected row only |
| Green on PASS rows. Make FAIL red on the word only, not the whole row | That way red is the only colored thing on screen, so it stands out |
| The `status: PASSED (v)` line in the detail pane | The selected row right next to it already shows the status |
| The `job:` label | The job name becomes the heading of the detail pane |

## After, at 72 columns

`FAIL` is red. The `api` row is in reverse video because it's selected. Nothing else is colored.

```
 BUILD MONITOR

 api      PASS                     | api
 web      PASS                     | duration  2m 10s
 worker   FAIL                     |
```

- **Borders:** down from three nested layers to one divider. Border characters go from 441 to 3.
- **Status:** each one now uses two signals: the word everywhere, plus red on failures only.
- **Selection:** the selected row is marked by reverse video alone.

## At narrower widths

The two panes need about 62 columns side by side, so a 60-column tmux split won't fit them. At that width, show the list by itself. Enter opens the detail view and Esc goes back. Because the list isn't visible in that view, the status goes back into the heading:

```
 BUILD MONITOR            |   api  PASS
                          |
 api      PASS            |   duration  2m 10s
 web      PASS            |
 worker   FAIL            |   Esc back
      (list view)                (after Enter)
```

If the terminal is too small to show even one list row, display a clear "terminal too small" message with the size needed, instead of a broken layout.
