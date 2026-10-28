Both problems are covered in one file: **`references/visual-patterns.md`**. Spinners are under *Progress indicators → Spinners* (line ~492). Table alignment is under *Tables and lists → Emoji and aligned columns* (~424) and *Localization → Ambiguous-width characters* (~442). Your framework's ecosystem reference names the exact width function to call.

## Root cause of the misalignment

Your code is almost certainly counting bytes or code points instead of **terminal cells**. `len()`, `.length` and `String::len()` all give the wrong number for CJK and emoji.

| Ecosystem | Measure with | Source |
|---|---|---|
| Go / Lipgloss | `lipgloss.Width()` (handles graphemes and skips ANSI) | `ecosystem-go.md:123` |
| Rust / Ratatui | `Line::width()` / `Span::width()`; use `s.cell_width()` (0.30.1+) for anything that must match what Ratatui draws | `ecosystem-rust.md:484` |
| TS / Ink | `string-width`, never `.length` | `ecosystem-typescript.md:375` |
| Python | a `unicode_width`-style cell-width function | `visual-patterns.md:667` |

## Rules for the table

1. **Pad and truncate by cell width.** CJK characters take 2 cells each. When you truncate, reserve 1 cell for `…` or 3 for `...`. Never wrap text inside dense table cells. Show the full value in a detail view instead.
2. **Emoji come in two kinds:**
   - Emoji with a **wide base**, like `✅ ❌ ⭐` and most pictographs, take 2 cells in every terminal. They're safe if you measure correctly.
   - Emoji built from a **narrow base plus a variation selector or joiner**, like `⚠️` (U+26A0 + U+FE0F), `✔️`, `❤️` and ZWJ families, take 1 or 2 cells depending on the terminal and the width library. That makes a column misalign by one cell per row, and it's the usual cause of "almost aligned" columns.
   - **Recommendation:** in status columns, use narrow symbols (`✓ ✗ !`) or words. If you keep emoji, stick to the wide-base ones, measure with a grapheme-aware library, and test on every terminal you support.
3. **Watch ambiguous-width characters.** Box-drawing borders, block elements, `▲▼▶◀`, `● ■ ★`, `…`, `·`, `•` and the arrows can render as 1 or 2 cells depending on the terminal's setting. go-runewidth switches to wide under `ja`/`ko`/`zh` locales, so CJK users in particular can end up with broken borders. Where you can, use narrow markers (`▸ ▾ ▴ ◉ ◦ ⋅ ✓ ✗ ⋯`). Keep ASCII borders one switch away. Test with the terminal's "ambiguous = wide" option turned on.
4. **Don't rely on emoji alone.** Some terminals render them as boxes, so pair them with a letter or word.
5. **Grapheme mode (2027):** if the terminal supports it, enabling it makes emoji sequences take the width your app calculated. Bubble Tea turns it on; the other frameworks don't (`terminal-protocols.md:40`). Even with it, test rows with lots of emoji.

## Rules for the status-bar spinner

- **Frames:** Braille `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` at about 80ms per frame. These are narrow, so the spinner won't shift the text after it, unlike ambiguous-width glyphs such as `●` or `◐`.
- **Delay:** show it only after 100–200ms so fast work doesn't flash a spinner.
- **Ending:** replace it with a final state, `✓` for success or `✗` for failure, or remove it. Never leave a frozen frame.
- **Non-TTY:** don't show it at all. CI logs shouldn't contain spinner frames.
- **Plain, screen-reader or reduced-motion mode:** print one static line (`Working...`) and then the final status. Give motion a named off switch and document it, like `GH_SPINNER_DISABLED` or `TEXTUAL_ANIMATIONS=none`.
- **Redraws:** redraw only on spinner ticks, not in an unconditional loop. The work behind the spinner must not block the UI thread.
- **Status messages:** start each with a symbol or label (`✓ Saved`, `✗ Save failed`) so they still make sense under `NO_COLOR`. Success messages fade after 3–5 seconds. Errors stay until dismissed and also go to a message log the user can reopen.

## Tests to add

Add golden-frame tests at 80×24 and at 60 columns. Use rows that mix CJK, combining marks, wide-base emoji and VS16 emoji, plus a truncated CJK cell. Run them once with the ambiguous-width setting on and once with ASCII fallback.

If you tell me your framework, or paste the table's rendering code, I can point to the exact line that's mismeasuring.
