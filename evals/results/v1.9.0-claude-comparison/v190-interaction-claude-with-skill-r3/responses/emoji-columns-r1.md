The two emoji are built differently, and terminals don't agree on how wide one of them is.

## Why it happens

- **✅ (U+2705)** is a single character that Unicode classes as East Asian **Wide**. Every terminal and width library gives it **2 cells**, so it's consistent.
- **⚠️ is two code points**: U+26A0 (⚠, which is **narrow**) followed by U+FE0F, a variation selector that asks for emoji presentation. Whether that pair takes **1 or 2 cells** depends on the terminal and on your width library. One may say 1 while the other draws 2, or the reverse.

When your code and the terminal disagree, every ⚠️ row is off by one cell and the columns after it shift. That explains "only in some terminals": the ✅ rows line up everywhere, and the ⚠️ rows only line up where the two sides happen to agree.

If you pad with `len()`, `.length` or byte counts, it gets worse. Those count code points or bytes, not cells, so they're wrong for both emoji.

## What to do

**1. Recommended: use narrow text symbols plus a word in the status column.**

```
STATUS     NAME
✓ ok       api-gateway
! warn     worker-3
✗ fail     scheduler
```

`✓ ✗ !` are reliably 1 cell. The word means the status still reads when color or Unicode is missing. Also add an ASCII fallback (`[ok]`, `[!]`, `[X]`) for piped output, `TERM=dumb`, or a non-UTF-8 locale.

**2. If you want to keep emoji:**
- Use only emoji whose base character is Wide, such as `✅ ❌ ⭐ 🔴 🟡`. For example, `🟡` or `❗` instead of `⚠️`. Avoid any emoji that relies on U+FE0F or a joiner (`⚠️`, `✔️`, `❤️`, ZWJ sequences).
- Measure cell width with a grapheme-aware library instead of string length:
  - Go: `lipgloss.Width()`
  - Rust: `unicode-width`
  - Python: `wcwidth` (Rich and Textual measure it for you)
  - JS/TS: `string-width`
- Test the table on the terminals you actually support. A library alone can't guarantee the terminal will agree with it.

**3. Don't use the emoji as the only signal.** Some terminals and fonts show tofu boxes. Keep a word next to it or in its own column.

**Quick check:** In the same table, put a row with `✅` and a row with `⚠️` in a fixed-width column, followed by a `|`. If only the ⚠️ row's `|` moves, this is your problem.

If you tell me your language or framework, I can show the exact padding code.
