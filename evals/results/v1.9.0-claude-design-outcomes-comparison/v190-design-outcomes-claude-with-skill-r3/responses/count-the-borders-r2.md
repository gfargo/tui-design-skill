The screen feels busy because of three things: three boxes nested inside each other, each status said four ways, and a detail pane that mostly repeats the list. Only about 1 in 20 of the visible characters is information you can't find somewhere else on the screen.

## The audit

| Check | Count |
|---|---|
| **Boxes inside boxes** | **3**: outer frame → panel → inner box → content. One is the useful limit, and here even one isn't needed. |
| **Ways each status is shown** | **4** in the list: `[PASS]` + `ok` + `v` + green (and `[FAIL]` + `fail` + `x` + red). The detail pane shows api's status twice more: `PASSED` + `(v)`. That's 6 for one fact. The limit is one color plus one word or symbol. |
| **Markers on every row** | `>` appears on 3 of 3 rows, so it marks nothing. It also hides which row is actually selected. |
| **Space spent on decoration** | 444 of 537 visible characters (83%) are border characters. Only about 29 characters are information that appears just once: 3 job names, 3 status words, and one duration. |
| **Duplicated pane** | In the detail pane, `job: api` repeats the selected row and `status: PASSED (v)` repeats its status. The only new fact is `duration: 2m 10s`. |

## What to remove

1. **The outer frame** (the `+---+` around the whole screen). The terminal edge already frames the app.
2. **Both panel borders and both inner boxes.** No box separates anything that whitespace can't.
3. **The `>` on every row.** Show the selected row with reverse video (swapped foreground and background) instead.
4. **The brackets in `[PASS]` and `[FAIL]`.** Keep just the word.
5. **The `ok` and `fail` column.** It repeats the status word.
6. **The `v` and `x` column.** It's a third copy of the status.
7. **Green on PASS rows.** Leave passes in the default text color so the red failure stands out. When 2 of 3 rows are colored, the color stops meaning anything.
8. **The whole detail pane at this width.** Move `duration` into a list column, and the `job:`, `status:` and `duration:` labels go with the pane.

## After (72 columns)

```
 BUILD MONITOR

 Job       Status  Duration
 api       PASS    2m 10s
 web       PASS    --
 worker    FAIL    --
```

- The `api` row is in reverse video because it's the selected row (the job your detail pane was showing).
- Only `FAIL` is red. The word and the color are its two signals, and passes get no color at all.
- The screen has no borders. Visible characters drop from 537 to 62.
- `--` marks durations I don't have. Your screen only showed api's, so fill the others in from your build data.

## At smaller sizes

- **80×24 and a 60-column tmux split:** this is already a single-pane layout, so nothing hides. The narrowest version needs about 27 columns. If `worker` is replaced by longer job names, cut them short with `…` instead of wrapping them.
- **Below about 30 columns:** show a "terminal too small, need 30 columns" message instead of a broken layout.
- **If you want a detail view back:** make it open on Enter and close on Esc. Only bring back a permanent side pane at 120+ columns, and only if it shows something the list doesn't, like a log tail, commit, or failing test name. A pane that repeats the selected row is exactly what made this screen busy.
