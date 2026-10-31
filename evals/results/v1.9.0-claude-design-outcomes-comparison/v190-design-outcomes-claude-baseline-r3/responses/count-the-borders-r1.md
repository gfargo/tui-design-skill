The busyness comes from three things: too many boxes, the same status shown four times, and a marker on every row that doesn't mark anything.

## What to remove

1. **Both inner boxes in each pane.** You currently have four borders between the screen edge and the text: outer, pane, inner, then text. One outer frame and one vertical divider are enough to separate the list from the detail pane. The other borders add lines without adding information.
2. **`ok` / `fail`** in the list rows. The row already says `[PASS]` or `[FAIL]`.
3. **`v` / `x`** at the end of each row. That's the third copy of the same status.
4. **The brackets around `PASS` / `FAIL`.** The row colour already sets the word apart, so the brackets are extra.
5. **`>` on unselected rows.** A marker on every row can't show which one is selected. Keep it only on the selected row.
6. **`(v)` after `PASSED`** in the detail pane. It's a fourth copy of the status.
7. **The `job:` label.** The job name works as the heading of the detail pane without a label.
8. **The separate title row.** Put `BUILD MONITOR` in the top border instead. That saves a line and a rule.

## After

```
+- BUILD MONITOR -------------------+----------------------------------+
| > api      PASS                   | api                              |
|   web      PASS                   | status    PASSED                 |
|   worker   FAIL                   | duration  2m 10s                 |
+-----------------------------------+----------------------------------+
```

The screen is still 72 columns wide and goes from 10 lines to 5. Each row now shows its status once (the word plus its colour), and only the selected row has a marker. Keep the green/red colour on just the `PASS`/`FAIL` word, not the whole row, so the job names are easier to scan.
