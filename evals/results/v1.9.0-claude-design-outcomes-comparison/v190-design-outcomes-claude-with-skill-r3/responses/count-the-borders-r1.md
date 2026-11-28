The busy feeling comes from three stacked boxes, every status shown four ways, and a marker on every row. About 95% of the non-blank cells on the screen are chrome and only about 5% are data.

## The clutter audit (counted at 72 columns)

| Check | Now | Budget |
|---|---|---|
| Border depth from the terminal edge to the content | **3** on both sides (outer frame → panel → inner box) | 1 at most |
| Signals for one status | **4**: `[PASS]` + green + `ok` + `v`. Same for FAIL: `[FAIL]` + red + `fail` + `x` | 1 color + 1 non-color |
| Markers on every row | `>` on 3 of 3 rows, and the `v`/`x` column on 3 of 3 rows | Only on exceptions |
| Chrome vs. data | 537 non-blank cells, 444 of them (83%) border characters. Only 29 cells are new data (job names, status words, `2m 10s`) | — |
| Detail pane | 3 fields, 2 of which (`job: api`, `status: PASSED (v)`) repeat the list. Only `duration` is new | — |

One extra problem: because every row has `>`, you can't tell which row is selected, so the detail pane's `api` has nothing on screen pointing to it.

## Exactly what to remove

1. **The outer full-screen frame.** The terminal edge already frames the app.
2. **Both inner boxes** (the `+---+` inside each panel). They wrap content that's already inside a panel, so they separate nothing.
3. **Both panel borders.** Replace them with one vertical rule between list and detail. That's the only border here doing real work: it separates two adjacent panes.
4. **The `[ ]` brackets** around PASS/FAIL.
5. **The `ok` / `fail` column.** It repeats the status word.
6. **The `v` / `x` column.** It's the third copy of the status.
7. **The `>` on every row.** Show the selected row with reverse video instead.
8. **Green on the PASS rows.** Leave passes plain and color only the word `FAIL` red, not the whole row. Failure then gets two signals (the word and red) and passes get none, so the exception stands out.
9. **`job: api`** in the detail pane. Use the job name as the pane title instead of a labeled field.
10. **`status: PASSED (v)`** in the detail pane. It duplicates the list, and it also says `PASSED` where the list says `PASS`.

## After

```
 BUILD MONITOR

 api       PASS                      | api
 web       PASS                      | duration  2m 10s
 worker    FAIL                      |
```

- The `api` row is in reverse video (that's the selection). `FAIL` is red. `BUILD MONITOR` and the detail title `api` are bold. `duration` is dim.
- The result is 5 rows instead of 10, with 55 non-blank cells instead of 537. Chrome drops from 508 cells to 26 (title, three divider cells, one label, one title), and all the data is still there.
- Use `│` for the divider if the terminal supports UTF-8, and keep `|` as the ASCII fallback.

## At smaller sizes

- **80×24:** Same layout. Nothing needs to change.
- **60-column tmux split:** Two panes with minimums of about 30 columns don't fit, so drop the detail pane. It holds just one field now, so move `duration` into a third list column (`worker    FAIL   3m 02s`) and open full details with Enter.
- **Below that:** Truncate job names with `…` and keep the status column. Under about 20 columns, show a "terminal too small, need 20 columns" message instead of a broken layout.

If every job has a duration (it almost certainly does), I'd use the single-table version at every width. The detail pane only earns its space once it holds more than the list does, like logs, the failing step, or a commit.
