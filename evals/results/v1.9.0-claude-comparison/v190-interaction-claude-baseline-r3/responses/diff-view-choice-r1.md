The directory is empty, so this is a general recommendation, not one fitted to your code.

## Use unified at 100 columns and side-by-side at 160

Base the choice on how much code each pane can show, not on how wide the terminal is.

| | Gutter | Code width per line |
|---|---|---|
| **100 cols, split** | 2 × ~7 (line no. + sign) + 3 divider | **~41 chars**, so most lines wrap. Don't use it. |
| **100 cols, unified** | ~12 (old no. + new no. + sign) | **~88 chars**, which fits nearly all code. |
| **160 cols, split** | 2 × ~7 + 3 | **~71 chars**, which fits most code. |

**Rule:** use split when `(width - 3) / 2 - gutter >= ~72`. That works out to about 150 columns. Two improvements make it work better:

- **Check the content too.** If every line in the hunk fits in a pane, you can use split below the threshold. If a hunk has lots of 120-character lines, stay unified even at 160.
- **Add hysteresis.** For example, switch to split at ≥152 and back to unified at ≤144, so the layout doesn't flip back and forth while someone resizes the window.
- **Let the user override it.** Add a key to toggle the mode (e.g. `s`), save the choice, and show the current mode in the status bar (`[split]` / `[unified]`).

## Mockups

**100 columns, unified:**
```
 @@ -41,7 +41,8 @@ func render(w int) {
  41  41   │   lines := wrap(text, w)
  42      - │   for _, l := range lines {
      42  + │   for i, l := range lines {
      43  + │       if i >= maxRows { break }
  43  44   │       out = append(out, l)
```

**160 columns, split:**
```
 @@ -41,7 +41,8 @@ func render(w int)
  41   lines := wrap(text, w)            │  41   lines := wrap(text, w)
  42 - for _, l := range lines {         │  42 + for i, l := range lines {
                                        │  43 +     if i >= maxRows { break }
  43       out = append(out, l)         │  44       out = append(out, l)
```

## Details that matter in both modes

1. **Highlight changes within lines.** In unified mode the old and new lines aren't next to each other, so highlighting just the changed words is what makes a one-character change easy to spot. Pair the removed and added lines in each block, then diff them by token.
2. **Don't rely on color alone.** Always show the `+`/`-` signs. Use a dim background for changed lines and a stronger one for changed words, so it still reads in 16-color terminals, with `NO_COLOR`, and for colorblind users.
3. **Long lines:** truncate them by default with a marker like `…` and offer a wrap toggle. In split mode, wrapping must keep the two sides lined up: if the left line wraps to 3 rows, add 2 blank rows on the right.
4. **Fill blank space in split mode.** Where one side has no line, use a faint hatch or a blank background so it doesn't look like a blank line in the file.
5. **Measure text correctly.** Expand tabs to a fixed width (4 or 8) before measuring, and use `wcwidth` for CJK characters and emoji. Otherwise the columns will drift.
6. **Collapse unchanged lines.** Show about 3 lines of context and fold the rest into `⋯ 37 unchanged lines` that the user can expand. This matters more at 100 columns, where vertical space is tighter.
7. **Keep the gutter fixed.** Size the line-number column from the largest line number in the file, not in each hunk, so the code column doesn't shift as the user scrolls.

If you tell me which framework you're using (Ratatui, Bubble Tea, Textual, Ink, etc.), I can sketch the layout and width-detection code for it.
