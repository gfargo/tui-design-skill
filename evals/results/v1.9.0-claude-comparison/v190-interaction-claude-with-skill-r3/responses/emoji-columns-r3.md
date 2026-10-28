**Short answer:** `✅` and `⚠️` are different kinds of emoji, and only `⚠️` causes the problem. Swap it for a narrow text symbol, or pair the status with a word, and measure width in terminal cells, not string length.

## Why it happens

- **`✅` (U+2705)** has an East Asian Wide base character. Every terminal and width library agrees it takes **2 cells**.
- **`⚠️`** is two code points: **U+26A0 ⚠**, which is a narrow character, plus **U+FE0F**, a variation selector that asks for emoji presentation. Whether that pair takes 1 or 2 cells depends on the terminal and on the width library your code uses. Some draw it 2 wide, some 1. Some draw a 2-wide glyph but move the cursor only 1 cell. When your padding math and the terminal disagree, every row with `⚠️` is off by one cell.

There are two other common causes:
- **Measuring with `len()` or `.length`** counts bytes or code units, not cells. `⚠️` is 6 bytes in UTF-8 and has a JS length of 2, but displays as 1 or 2 cells.
- **Grapheme mode (terminal mode 2027):** where a terminal supports it and the app turns it on, the terminal uses the width the app computed. Bubble Tea turns it on; most other frameworks don't. Without it, the app and the terminal can still disagree.

## What to do

1. **Use narrow text symbols or words for status.** This fully fixes it:
   ```
   STATUS
   ✓ ok
   ! warn
   ✗ fail
   ```
   `✓ ✗ !` are narrow in every terminal. Avoid `● ▲ ★ •` as replacements: they're "ambiguous-width" and break when a terminal treats ambiguous characters as wide.

2. **If you want to keep emoji,** only use ones with a wide base character, like `✅ ❌ ⭐`. Drop `⚠️`, `✔️`, `❤️` and ZWJ sequences. Even with wide-base emoji, measure with a grapheme-aware width function:
   - Go: `lipgloss.Width()`. Don't use `len()`.
   - Rust: the `unicode-width` crate (Ratatui uses it internally).
   - Python: `rich.cells.cell_len` or `wcwidth.wcswidth`.
   - JS/TS: `string-width`.

3. **Don't let the emoji be the only signal.** Some terminals and fonts show a box or `?`, and screen readers announce it inconsistently. Put a word next to it, or rely on the word alone. If color is also on, you already have three signals for one state (glyph, color, word), and that's plenty. Don't add a row marker as well.

4. **Add an ASCII fallback** (`[ok]`, `[!]`, `[x]`) when output is piped, the locale isn't UTF-8 (check `LC_ALL`, then `LC_CTYPE`, then `LANG`), or the user passes something like `--ascii`.

5. **Test it:** add a golden test of a status column that mixes `ok` and `warn` rows. Then check the table by eye in the terminals you support, including tmux and one with the "ambiguous characters are wide" setting on (iTerm2, GNOME Terminal and Windows Terminal all have it).

If you tell me your language or framework, I can point to the exact place in your table code to change.
