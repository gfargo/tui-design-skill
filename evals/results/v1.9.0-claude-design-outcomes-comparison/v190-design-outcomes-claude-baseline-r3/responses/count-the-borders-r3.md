It feels busy because of two things: **every status is shown four times**, and **there are three borders where one would do**. Remove these:

**Status shown four times per row**
1. **The `ok` / `fail` column.** It repeats `[PASS]` / `[FAIL]`.
2. **The `v` / `x` column.** Same information a third time.
3. **The `(v)` after `PASSED` in the detail pane.** Same again.

Keep `[PASS]` / `[FAIL]` along with the color. The text is what makes it readable for colorblind users and on terminals without color.

**`>` on every row**
4. **The `>` on rows that aren't selected.** A cursor only helps if it marks one row. On every row it just reads as a bullet.

**Three nested borders**
5. **The inner box in each panel.** It wraps the same content as the panel box around it.
6. **The two panel boxes.** One vertical divider separates list from detail just as well.
7. **The separate title row.** Put `BUILD MONITOR` in the top border instead. That saves a line and one more horizontal rule.

That takes the screen from 11 lines to 5 and from 8 boxes to 1, and each fact now appears once.

```
+- BUILD MONITOR ------------------------------------------------------+
| > api       [PASS]               | job:      api                     |
|   web       [PASS]               | status:   PASSED                  |
|   worker    [FAIL]               | duration: 2m 10s                  |
+----------------------------------------------------------------------+
```

Every line is still 72 columns. The `[PASS]`/`[FAIL]` labels stay green and red. To make the selection stand out more, show the `>` row in reverse video or bold rather than adding back more symbols.
