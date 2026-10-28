## Why it happens

The two emoji are built differently.

| Glyph | Codepoints | What width tables say | What terminals do |
|---|---|---|---|
| ✅ | `U+2705` | Emoji by default, East Asian Width **Wide**, so **2 cells** | Nearly all agree: 2 |
| ⚠️ | `U+26A0` + `U+FE0F` (variation selector-16) | Base char is **Narrow/Neutral** (1) and VS16 is zero-width, so **1 cell** | **They disagree:** 1 or 2 |

`U+26A0` is a text-style symbol. The invisible `U+FE0F` after it asks for the colorful emoji version. Unicode doesn't clearly say whether that request should also change the width, so terminals handle it differently:

- **Some count it as 1 cell** (they follow the classic `wcwidth` tables). The emoji then draws over the next character, or your padding looks one cell too short.
- **Some count it as 2 cells** (newer ones, e.g. WezTerm, Ghostty, kitty, and recent iTerm2 depending on settings). If your padding assumed 1, that row ends up one cell too wide.
- Your **width library** (`wcwidth`, `string-width`, `unicode-width`, etc.) has its own opinion, which may not match the terminal.

The row breaks wherever your code's width count and the terminal's differ. Also, if you pad using `len()` / `.length`, ⚠️ counts as 2 code points and ✅ as 1, so both are wrong in different ways.

## What to do

In order of how reliable each fix is:

1. **Avoid emoji that need VS16.** Use only emoji whose default form is already emoji-style and 2 cells wide, so every terminal agrees:
   - ✅ `U+2705`, ❌ `U+274C`, ⛔ `U+26D4`, 🟡 `U+1F7E1`, 🔴 `U+1F534`, 🟢 `U+1F7E2`
   - For example, swap ⚠️ for 🟡 or ⛔.

2. **Or skip emoji and use 1-cell symbols with color:** `✓` `✗` `!` `●` `▲`, colored green/yellow/red with ANSI codes. Widths are predictable, and the table works in plain-text logs and over SSH too. This is what most mature CLIs do.

3. **Measure display width, never string length.** Use `wcwidth.wcswidth()` in Python, `string-width` in JS, `unicode-width` in Rust, or `go-runewidth`. This fixes the `len()` problem but **not** the ⚠️ disagreement, because the library can only pick one answer. So combine it with #1 or #2.

4. **Put the status in the last column.** If a width guess is off, nothing after it shifts. It's a cheap workaround if you have to keep ⚠️.

5. **Advanced: measure at runtime.** Print the glyph, ask the terminal where the cursor ended up (`ESC[6n`), and use that width. Some terminals also support mode 2027 (grapheme clustering) to make VS16 handling consistent. This is usually more trouble than it's worth for a status column.

**My recommendation:** use 🟡 or ⛔ instead of ⚠️ and keep ✅ (all 2 cells), and pad with a width library. If the output might end up in logs or CI, use colored `✓` / `!` / `✗` instead.

If you show me the table-rendering code, I can make the change.
