The short version: remove the inner box, the `>` on every row, and two of the three status signals. Then let column alignment and whitespace provide the structure.

## Where the noise comes from

Your list probably looks something like this (`PASS` in green, `FAIL` in red):

```
+--------------------------------------+
| +----------------------------------+ |
| | > [PASS] (ok)  build        2.1s | |
| | > [PASS] (ok)  lint         0.8s | |
| | > [FAIL] (!!)  test         4.5s | |
| +----------------------------------+ |
+--------------------------------------+
```

1. **Two borders deep.** Count the borders between the terminal edge and the text: there are two. The inner box sits inside a box that already separates the content, so it does nothing. The outer box is usually redundant too, because the terminal edge already frames the app.
2. **Three signals for one fact.** `[PASS]`, `(ok)` and green all say the same thing. A good limit is one color cue plus one non-color cue.
3. **A marker on every row.** When `>` appears on 100% of rows, it doesn't mark anything. If it's meant to show the selected row, it can't, because every row has it.
4. **Mostly chrome.** In a three-row list like this, about 84% of the non-blank cells are borders, brackets, markers and repeated tags. Only about 16% are task names and times. That ratio is what makes it feel busy.

## What to cut

| Element | Action | Why |
|---|---|---|
| Inner border | Delete | It separates nothing |
| Outer border | Delete, unless this panel sits next to other panels | The terminal edge frames it already |
| `>` on every row | Delete. Show the selected row with reverse video only | A marker on every row carries no information |
| `(ok)` / `(!!)` | Delete | Duplicates the tag |
| `[` `]` around the status | Delete | The column position already marks it as a status |
| Green on PASS | Optional. Dropping it makes failures stand out more | Passing rows are the normal case |

## After

```
 Task    Status  Time
 build   PASS    2.1s
 lint    PASS    0.8s
 test    FAIL    4.5s      ← FAIL in red; selected row in reverse video
```

There are no borders now. A failure has exactly two signals: the word and red. Passing rows have little or no emphasis. The only chrome left is one header row. Right-align the time column so durations line up for comparison.

If the list is long, a single summary line above the header helps more than any decoration: `2 passed ⋅ 1 failed`. You could also sort failures to the top.

## At smaller terminal sizes

- **80×24:** Keep the header row fixed and scroll the rows under it. Virtualize the list if it can grow to hundreds of tests.
- **60-column tmux split:** Keep `Status` and `Time` at fixed widths. Cut long task names from the end with `…` instead of wrapping them. Put the full name in a detail view opened with Enter.
- **Below about 30 columns:** Don't draw a broken layout. Show `terminal too small: need 30 columns`, and make sure `q` and Ctrl+C still quit.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink…), I can show the exact table and style code for this.
