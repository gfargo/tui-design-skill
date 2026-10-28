The working directory is empty, so I can't point you at specific files. Here's where these bugs usually come from and the rules for fixing them. If you share the code or tell me your language/framework, I can find the exact lines.

## Where to look

1. **The width function.** Look for any place that sizes, pads or truncates a cell using `len(s)`, `.length`, `str.len()` or a rune/char count. That's almost always the bug, because those count bytes or code points, not terminal columns.
2. **Table layout.** Check the code that computes column widths (usually a max over the cells), then the pad/truncate helpers that use those widths.
3. **Status bar layout.** Check where it works out "remaining space" after the spinner, and the list of spinner frames.
4. **ANSI styling.** If you measure a string after adding color codes, the escape sequences get counted as visible width.

## The rules

**1. Measure in terminal cells, not characters.** Use a width library:

| Language | Library |
|---|---|
| Go | `go-runewidth`, `rivo/uniseg` (lipgloss uses these) |
| Rust | `unicode-width` + `unicode-segmentation` (ratatui) |
| JS/TS | `string-width`, `strip-ansi` |
| Python | `wcwidth`, or `rich.cells.cell_len` |

**2. Width per character:**
- ASCII and most Latin text: 1 cell
- CJK (East Asian Width W/F), fullwidth forms and emoji: 2 cells
- Combining marks, ZWJ (U+200D) and variation selectors: 0 cells
- "Ambiguous" characters such as `●`, `◐`, `±`, `…` and some box-drawing: 1 cell normally, but 2 in some CJK-locale terminals

**3. Work in grapheme clusters, not code points.** `👨‍👩‍👧` (a ZWJ sequence), `🇯🇵` (a flag) and `👍🏽` (a skin tone) are each one visible unit 2 cells wide. Summing per-code-point widths overcounts them.

**4. Watch out for VS16 emoji.** Characters like `❤️`, `☀️` and `✔️` are a 1-cell base plus U+FE0F. Terminals disagree on whether they take 1 or 2 cells. This is the most common cause of a single row being off by one. The safest fix is to avoid them in aligned columns, or swap them for unambiguous glyphs.

**5. Pad and truncate by cells:**
- Padding is `target - display_width(s)`.
- When truncating, never split a grapheme cluster. If a 2-cell character would cross the column edge, drop it and pad with a space instead.
- Leave room for the ellipsis, and count its own width.
- Strip ANSI codes and expand tabs before you measure.

**6. Spinner rules:**
- Every frame must be the same width. Put the spinner in a fixed-width slot so the rest of the status bar never moves.
- Prefer Braille frames (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`). They're always 1 cell.
- Avoid emoji spinners (🌑🌒…) and ambiguous ones (◐◓◑◒) if users might have CJK locales. If you do use them, reserve 2 cells.
- Redraw only the spinner cell, not the whole line. Hide the cursor, throttle to about 80–120 ms, and turn the spinner off when output isn't a TTY.

**7. Alignment:** compute column widths in cells across all rows. Left-align text and right-align numbers.

**8. Test across terminals** (iTerm2, Terminal.app, kitty, WezTerm, tmux) with a fixture row containing `中文`, `👨‍👩‍👧`, `❤️`, `🇯🇵` and `é` (e + combining accent). Rows that are still off in only one terminal are a terminal disagreement, not your bug. Pick a convention and keep those characters out of tight columns.
