## Why it happens

The two symbols aren't the same kind of character, even though they look alike:

| Glyph | Codepoints | What it is | Width |
|---|---|---|---|
| ✅ | `U+2705` | Emoji by default (`Emoji_Presentation=Yes`, East Asian Width = **W**) | 2 columns, almost everywhere |
| ⚠️ | `U+26A0` + `U+FE0F` | A text symbol (width **N**, 1 column) plus Variation Selector-16, which asks for emoji display | **Depends on the terminal**: 1 or 2 |

Your table code (or `wcwidth`, `string-width`, `unicode-width`, etc.) works out a width for each cell and pads it. The terminal then draws the glyph at whatever width *it* thinks is right. For ⚠️ those two answers often differ:

- Older wcwidth tables ignore VS16, so they count `⚠️` as 1 column. Newer ones count it as 2.
- Terminals differ too. iTerm2, Kitty, WezTerm and Windows Terminal usually draw it 2 wide. Some versions of Terminal.app, GNOME/VTE, tmux and many SSH/CI viewers draw it 1 wide, or draw it 2 wide but only move the cursor 1.
- tmux and screen run their own width logic, which adds another place for the answers to disagree.

So the row with ⚠️ ends up one column off, while the ✅ rows line up. Padding can't fix this, because you can't know at runtime what width the terminal will use.

## What to do

Pick symbols that every terminal agrees on. In order of robustness:

1. **Use plain single-width text symbols** (most reliable):
   ```
   ✓ ok     ✗ fail     ! warn     • pending
   ```
   `✓ ✗ ! •` have no emoji form and no variation selector, so they're 1 column everywhere. Add color (green/yellow/red) to keep them easy to scan.

2. **If you want emoji, use only ones that are wide by default:**
   ```
   ✅ ok     ❌ fail     🟡 warn     ⏳ pending
   ```
   These are all `Emoji_Presentation=Yes` with no VS16, so they're consistently 2 columns. Avoid anything that needs `U+FE0F` to look like an emoji: ⚠️ ℹ️ ✔️ ❤️ ☑️ ▶️.

3. **Put the status column last.** If nothing comes after it, a width mismatch can't push later columns out of line.

4. **Offer an ASCII fallback.** Print `[OK]`, `[WARN]` and `[FAIL]` when output isn't a TTY, when `TERM=dumb`, or behind a flag like `--ascii`. Logs, CI and screen readers are better served by that anyway.

5. **Measure with a current, grapheme-aware width library** (`wcwidth` ≥ 0.2.9 in Python, `string-width` in JS, `unicode-width` in Rust). Don't use `len()` or `.length`. This fixes the mistakes on your side, but it won't fix a terminal that disagrees, so do it along with 1 or 2, not instead of them.

**Quick fix:** swap ⚠️ for 🟡 (or for a yellow `!`), and the columns should line up again.
