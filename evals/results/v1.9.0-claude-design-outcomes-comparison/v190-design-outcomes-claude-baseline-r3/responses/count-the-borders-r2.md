The busyness comes from two things. The layout is boxed three times over, and every status is shown four times: the color, `[PASS]`, `ok` and `v`. Neither adds information.

**What to remove:**

1. **The two inner boxes in each pane.** You have a box inside a pane inside the outer frame. Keep the outer frame and split it with one vertical divider. Each removed box frees 4 columns and 2 rows of plain border.
2. **`ok` / `fail`.** These repeat PASS/FAIL.
3. **`v` / `x`.** These repeat it a third time.
4. **The brackets around PASS/FAIL.** The color already sets the word apart. Keep the word itself so the status still reads without color.
5. **The `>` on every row.** A marker on every row doesn't single anything out. Put `>` only on the selected row so it works as a cursor.
6. **The `status:` line in the detail pane.** The list already shows the selected job's status one column away. `(v)` repeated it a fifth time.
7. **The colons after the detail labels.** Lining up the values in a column already separates them from the labels.

**After:**

```
+----------------------------------------------------------------------+
| BUILD MONITOR                                                        |
+-----------------------------------+----------------------------------+
| > api      PASS                   | job       api                    |
|   web      PASS                   | duration  2m 10s                 |
|   worker   FAIL                   |                                  |
+-----------------------------------+----------------------------------+
```

PASS stays green and FAIL stays red. FAIL is now the only red word in a calm column, so it stands out much more than it did. The screen still fits in 72 columns and is one row shorter. If you add more detail fields later, the space you freed gives them room without adding clutter.
