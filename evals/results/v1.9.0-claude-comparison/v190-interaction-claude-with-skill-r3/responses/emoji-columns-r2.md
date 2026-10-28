**It's the ⚠️, not the ✅.** The two emoji belong to different Unicode width classes, and terminals don't agree on how wide ⚠️ is.

## Why

| Glyph | Code points | Width |
|---|---|---|
| ✅ | U+2705 | East Asian **Wide**. Every terminal and width library draws it as 2 cells. |
| ⚠️ | U+26A0 + U+FE0F (variation selector 16) | The base ⚠ is **narrow** (1 cell). The invisible U+FE0F asks for emoji presentation. Some terminals then draw it 2 cells wide and some keep it at 1. Width libraries disagree in the same way: classic `wcwidth` ignores VS16 and says 1, newer grapheme-aware libraries say 2. |

Your table code pads each cell using some width number. If the terminal draws ⚠️ one cell wider or narrower than that number, every cell to its right in that row shifts by one. ✅ rows stay aligned and ⚠️ rows don't, and the result changes from terminal to terminal.

If you pad with `len()`, `.length`, or a byte or code-point count, you have a second bug on top of this one. ✅ then misaligns everywhere, and ⚠️ counts as 2 "characters" (2 code points) no matter how it's drawn.

## What to do (best option first)

1. **Use narrow text symbols plus a word.** For example `✓ ok`, `! warn`, `✗ fail`. These are 1 cell everywhere, so the misalignment can't happen. They also pass the "never signal state with emoji alone" rule, because some terminals and fonts render emoji as boxes. Keep plain ASCII (`[ok]`, `[!]`, `[X]`) as a fallback for when output is piped or Unicode support is uncertain.

2. **If you want emoji, use only ones with a Wide base and no VS16.** Keep ✅ and swap ⚠️ for something like ❗ (U+2757), ⛔ (U+26D4), or 🟡. These are reliably 2 cells. Check any candidate in [EastAsianWidth.txt](https://www.unicode.org/Public/18.0.0/ucd/EastAsianWidth.txt): you want class `W`, and you don't want a trailing `FE0F`.

3. **Measure cell width with a grapheme-aware library.**
   - Go: `lipgloss.Width()`
   - Rust: `unicode-width`
   - Python: `wcwidth.wcswidth` or Rich's `cell_len`
   - JS: `string-width`

   This fixes the `len()` bug. It does **not** fully fix ⚠️, because the library can be right by the spec and the terminal can still draw it differently. Terminals that support grapheme mode (`CSI ? 2027 h`) follow the width the app computed. Bubble Tea turns this on for you; the other frameworks don't. Terminals without it can still disagree.

4. **A quick fix if you're stuck with ⚠️:** make status the last column. A one-cell error then only moves the end of the line, not every column after it.

## Two extra checks

- **Duplicate signals:** if the status cell already has a color and a word, the emoji is a third copy of the same information. A symbol plus a word is usually enough.
- **Test:** add golden or snapshot tests for rows containing ✅, ⚠️, CJK text, and combining marks. Then look at it in the terminals you actually support, including tmux. Snapshot tests check your width math, not how a given terminal draws the glyph.

If you tell me the language or framework, I can point you to the exact width function and table widget to use.
