Your folder is empty, so this is general advice rather than advice about your code. In short: **use a unified diff at 100 columns and a side-by-side diff at 160**. Pick the layout from the actual terminal width, and let the user override it.

## Why: column budget

**100 columns, side-by-side:**
- Splitting gives about 49 columns per pane.
- A gutter (4-digit line number, space, `+`/`-` sign, space) takes about 7, leaving **~42 columns of code**.
- Most code lines will wrap or get cut off, so this is too narrow.

**100 columns, unified:**
- The gutter holds the old line number, the new line number and the sign, about 12 columns.
- That leaves **~88 columns of code**. Most lines fit unchanged.

**160 columns, side-by-side:**
- Each pane is about 79 columns, leaving **~72 columns of code**.
- That's enough for most code, and seeing old and new next to each other makes changes much easier to read.

## Recommended behavior

1. **Choose by usable code width, not a fixed column count.** Calculate per-pane code width as `(cols - divider) / 2 - gutter`. Go side-by-side if that's at least ~70, or at least the 90th-percentile line length of the current diff. In practice the switch lands around **140–150 columns**.
2. **Add a toggle key (e.g. `s`)** to force unified or split. Remember the choice for the session.
3. **Re-check on resize (SIGWINCH).** Add some hysteresis, such as switching at 145 and back at 135, so dragging the window doesn't make it flicker. When the layout changes, keep the current hunk at the same screen position.
4. **Long lines:** truncate with `…` by default and let `←/→` scroll sideways, or offer wrapping as an option. If you wrap in split view, pad the shorter side with blank rows so the two panes stay aligned.
5. **Split-view alignment:** put changed lines opposite each other. Fill unmatched additions or deletions with blank or hatched filler rows so the context lines stay level across both panes.
6. **Highlight the changed words, not just the line.** Use a stronger background on the exact characters that changed. This matters most in unified view, where the old and new lines are stacked and harder to compare.
7. **Don't rely on color alone.** Always show the `+`/`-` sign so the diff still works without color (`NO_COLOR`, colorblind users, piping output). Dim the context lines.
8. **Hunk headers:** show `@@ -a,b +c,d @@` plus the enclosing function name, and give them a full-width background. Put the file name in a sticky header at the top.
9. **Size gutters to the file:** base line-number width on the largest line number, not a fixed 4 digits.

## Sketch

**100 columns (unified):**
```
 src/app.ts ─────────────────────────────────────────────────────────────
 @@ -40,6 +40,7 @@ function render()
  40  40   const width = term.cols;
  41     - const mode = "split";
      41 + const mode = width >= 145 ? "split" : "unified";
      42 + const gutter = digits(maxLine) + 3;
```

**160 columns (side-by-side):**
```
 src/app.ts ──────────────────────────────────────┬──────────────────────────────────────────────
  40   const width = term.cols;                   │  40   const width = term.cols;
  41 - const mode = "split";                      │  41 + const mode = width >= 145 ? "split" : …
                                                  │  42 + const gutter = digits(maxLine) + 3;
```

If you tell me your framework (Ratatui, Bubble Tea, Ink, Textual, etc.), I can show how to wire up the width check and resize handling in it.
