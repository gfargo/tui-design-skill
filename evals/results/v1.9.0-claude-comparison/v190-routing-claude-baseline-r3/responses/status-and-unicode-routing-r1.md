The working directory is empty, so I couldn't look at your code. Here's where these bugs usually come from and the rules for fixing them.

## Where to look

1. **Anywhere you measure text with string length.** `len(s)`, `s.length`, `utf8.RuneCountInString`, `.chars().count()` all count code points or bytes. You need terminal cells. Check column-width calculation, padding (`ljust`, `padEnd`, `%-20s`, `format!("{:<20}")`), truncation, and the status-bar code that works out how much room is left after the spinner.
2. **Truncation code.** It's probably slicing by index. That can split a wide character, a ZWJ emoji sequence, or a base character from its combining mark.
3. **The spinner's frame list.** If the frames have different widths, everything to their right shifts on each tick.

## Width rules

| Content | Cells |
|---|---|
| ASCII, Latin, Cyrillic, box-drawing `─│┌` | 1 |
| CJK ideographs, kana, Hangul, fullwidth forms (East Asian Width W/F) | 2 |
| Combining marks, ZWJ (U+200D), variation selectors, zero-width space | 0 |
| Emoji with default emoji presentation (😀 🚀) | 2 |
| Text-default symbol + VS16 (`❤️` = U+2764 U+FE0F) | 2 in most modern terminals, but wcwidth often says 1 ⚠️ |
| ZWJ sequences (👨‍👩‍👧), skin tones, flags 🇯🇵 | Should be 2 as one grapheme. Older terminals render the parts separately ⚠️ |
| East Asian **Ambiguous** (`…`, `●`, `◐`, `○`, `★`, `→`, `±`, Greek, some box/geometric shapes) | 1 normally, **2 in terminals set to "ambiguous = wide"**, which is common for CJK users ⚠️ |

Rules that follow from this:
- **Measure by grapheme cluster** (UAX #29), then add up each cluster's width. Don't measure code point by code point.
- **Pad with `target_width − display_width(s)` spaces.** Never use built-in padding that counts characters.
- **Truncate on grapheme boundaries.** If the next cluster is 2 wide and only 1 cell is left, stop and pad with a space.
- **Watch your ellipsis.** `…` is Ambiguous width. Use `...` or measure it the same way as everything else.
- **Leave a margin for ⚠️ cases.** Code and terminal can disagree on width, so don't fill a cell-exact layout with emoji. Keep emoji out of column edges, or put them at the end of a row where a 1-cell error doesn't shift anything after it.

## Spinner rules

- **Every frame must be the same width.** Width 1 everywhere: ASCII `| / - \` or Braille `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` (Braille is Neutral width, so it's safe).
- **Avoid `◐◓◑◒`, `●○`, `★`.** They're Ambiguous and become 2 cells in CJK-configured terminals. Since your app shows CJK text, there's a real chance some of your users have that setting on.
- **Avoid emoji spinners** like 🌑🌒🌓 or 🕐🕑. Their width varies by terminal and font.
- **Give the spinner a fixed slot** (for example, column 0 plus one space). Redraw only that slot, or redraw the whole line with `\r\x1b[2K`. Don't append to the line.
- **Hide the cursor** while it spins (`\x1b[?25l` / `\x1b[?25h`, and restore it on exit and on SIGINT). About 80–100 ms per frame is plenty.

## Libraries that get this mostly right

- **Python:** `wcwidth.wcswidth` (returns -1 for control characters, so handle that). `rich` uses `cell_len` internally.
- **Go:** `github.com/mattn/go-runewidth` (has an `EastAsianWidth` toggle) and `rivo/uniseg` for graphemes. `lipgloss.Width` wraps them.
- **Rust:** `unicode-width` and `unicode-segmentation`.
- **JS/TS:** `string-width` (Ink uses it). Add `Intl.Segmenter` for graphemes.

## Test strings

Paste these into a table cell and check that the right border lines up:
`abc`, `日本語`, `ｶﾀｶﾅ` (halfwidth, 1 cell each), `é` written as `e`+U+0301, `❤️`, `👨‍👩‍👧`, `🇯🇵`, `…`. Run them in at least two terminals (for example iTerm2/Ghostty and Terminal.app). If one terminal still misaligns on the ⚠️ rows, that's the terminal or its font fallback, not your code.

If you share the table and status-bar code, I can point to the exact lines.
