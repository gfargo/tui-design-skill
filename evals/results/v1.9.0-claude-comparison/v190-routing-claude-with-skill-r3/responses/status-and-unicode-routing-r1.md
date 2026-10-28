Everything you need is in one file: **`references/visual-patterns.md`**. For width APIs specific to your framework, also check its ecosystem reference.

## Where to look

| Problem | Section |
|---|---|
| Spinner behavior | *Progress indicators → Spinners* (line ~492), *Accessibility → Motion* (~649) |
| Status-line content | *Status bars, headers, footers → Status / mode line* (~460) |
| Emoji in columns | *Tables and lists → Emoji and aligned columns* (~424) |
| CJK and ambiguous-width glyphs | *Localization → Ambiguous-width characters* (~442) |
| Truncation | *Tables and lists → Truncation* (~389) |
| Width API for your stack | `ecosystem-go.md:123`, `ecosystem-rust.md:484`, `ecosystem-typescript.md:375` |
| Terminal-side grapheme mode | `terminal-protocols.md:40` (mode 2027) |

## Rules for the spinner

- **Use Braille frames.** `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`, about 80ms per frame. These are narrow-class, so they always take one cell. Avoid `● ◐ ▲ ■` and similar shapes. Those are East Asian *Ambiguous* width, and they make the status bar jitter on terminals set to render ambiguous characters wide.
- **Delay it.** Show the spinner only after about 100–200ms, so instant work doesn't flash it.
- **End on a final state.** Replace it with `✓` or `✗` plus a word, or remove it. Never leave a frozen frame.
- **Turn it off when it doesn't belong.** Suppress it on non-TTY output. In plain, screen-reader, or reduced-motion mode, print one static `Working...` line instead, and give users a named env var to disable it (like gh's `GH_SPINNER_DISABLED`).
- **Only tick while work is running.** Spinner ticks are the one intentional redraw loop. Stop the timer when the work finishes, and never block the UI thread on the work.
- **Lead status messages with a symbol or word.** For example `✓ Saved` or `✗ Save failed`, so the meaning survives `NO_COLOR`.

## Rules for table alignment

1. **Measure display cells, not string length.** `len()`, `.length`, and byte or code-point counts are all wrong. Use:
   - Go: `lipgloss.Width()`
   - Rust/Ratatui: `Line::width()`, or `s.cell_width()` (0.30.1+) for anything that must match what Ratatui draws
   - TS/Ink: `string-width`
   - Python: a cell-width function such as Rich's `cell_len` or `wcwidth`

   Use this one function to pad, truncate, and compute column widths everywhere.
2. **CJK takes 2 cells.** Pad to the column width in cells. When truncating, never split a wide character: if only one cell is left, fill it with a space.
3. **Emoji are the unreliable part.**
   - Emoji with a wide base character (`✅ ❌ ⭐` and most pictographs) take 2 cells everywhere.
   - Emoji built from a narrow base plus a variation selector or joiner (`⚠️` = U+26A0+U+FE0F, `✔️`, `❤️`, ZWJ families) take 1 or 2 cells depending on the terminal and the width library. That gives you one cell of drift per row.
   - **For status columns, use narrow symbols (`✓ ✗ !`) or words.** If you keep emoji, pick only wide-base ones, measure by grapheme cluster, and test on the terminals you support.
4. **Watch ambiguous-width characters.** This includes `…`, `·`, `•`, `●`, `▲▼`, arrows, box drawing and block elements. go-runewidth treats them as wide under `ja`/`ko`/`zh` locales, and most other libraries treat them as narrow. Prefer `▸ ▾ ▴ ✓ ✗ ⋅ ⋯`. Test with the terminal's "ambiguous = wide" setting turned on, and keep an ASCII border/bar fallback behind one switch.
5. **Truncate, don't wrap, in table cells.** Reserve one cell for `…`. Truncate paths from the start or middle, and names or prose from the end.
6. **Terminal mode 2027.** If the terminal supports grapheme-cluster mode 2027 (Bubble Tea enables it), emoji sequences take the width your app computed. Without it, app and terminal can still disagree.
7. **Don't use emoji as the only signal.** Some terminals render them as boxes, so pair them with a letter or word.

## Verifying the fix

Add golden-frame tests at 80×24 and 60 columns, with rows containing CJK, a combining mark, a wide-base emoji, a VS16 emoji (`⚠️`), and a truncated CJK string. Run them once with the terminal's ambiguous-width setting flipped.

If you tell me your framework, I can point you to the exact width call and check your padding and truncation code.
