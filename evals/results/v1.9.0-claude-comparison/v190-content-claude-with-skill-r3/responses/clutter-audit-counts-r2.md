Remove both boxes, keep one status signal per row, and drop the `>` from every row except the selected one. Here's the list counted the way "busy" can be measured.

## Why it feels busy

| Check | Your list | Target |
|---|---|---|
| Borders between the terminal edge and the rows | **2** (two nested boxes) | 0 or 1 |
| Signals for one status | **3**: `[PASS]`, `(ok)` and color | 1 color + 1 non-color at most |
| Markers on every row | `>` on **every** row | Only on the row that's different |
| Cells spent on chrome | About **84%** for a 3-row list | Mostly data |

The terminal edge already frames the app, so the outer box separates nothing. The inner box sits inside the outer one, so it doesn't mark focus either. A `>` on every row doesn't mark anything. `[PASS]` and `(ok)` say the same thing twice.

## What to cut

1. **Delete both boxes.** Use a header row and whitespace instead. Bring back one border only if this list later sits next to another pane and you need to show which one has focus.
2. **Delete `(ok)` / `(!!)`.** Keep the word `PASS`/`FAIL` (it still reads with `NO_COLOR`) plus color.
3. **Delete the brackets.** A `Status` column makes them unnecessary.
4. **Delete the always-on `>`.** Show the selected row with reverse video and nothing else.
5. **Optional:** color only `FAIL` (red) and leave `PASS` in the normal or dimmed text color. Then the failures stand out instead of three green tags.

Before:
```
+--------------------------------------+
| +----------------------------------+ |
| | > [PASS] (ok)  build        2.1s | |
| | > [PASS] (ok)  lint         0.8s | |
| | > [FAIL] (!!)  test         4.5s | |
| +----------------------------------+ |
+--------------------------------------+
```

After (`FAIL` in red, selected row in reverse video):
```
 Task    Status  Time
 build   PASS    2.1s
 lint    PASS    0.8s
 test    FAIL    4.5s          ← selected: reverse video only

 2 passed · 1 failed · 7.4s
```

This has no borders, one status column and no always-on markers. Only about a quarter of the cells are labels. The summary line at the bottom shows the overall result the boxes were hinting at.

## Check narrow widths too

Nested boxes cost 4 columns on each side, so removing them also helps in small terminals.

- **80×24:** fits easily. Right-align `Time` and keep a 2-cell gap between columns.
- **60-column tmux split:** give `Status` (6) and `Time` (≈6) fixed widths and let `Task` take the rest. Long task names end in `…` instead of wrapping, and the full name goes in a detail view (Enter).
- **Below your tested minimum (around 24 columns):** don't draw a broken table. Show `terminal too small: need 24 cols`, and keep `q` and `Ctrl+C` working.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink…), I can show the code that does this.
