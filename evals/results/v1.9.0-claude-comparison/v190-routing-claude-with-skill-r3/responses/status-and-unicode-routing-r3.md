Everything you need is in `references/visual-patterns.md`. Your framework's ecosystem reference has the exact function for measuring cell width.

## Where to look

| Problem | Section |
|---|---|
| Spinner rules | `visual-patterns.md:492` → *Progress indicators › Spinners* |
| Spinner with motion turned off | `visual-patterns.md:649` → *Accessibility › Motion* |
| Status-line messages | `visual-patterns.md:460` → *Status / mode line* |
| Emoji in table columns | `visual-patterns.md:424` → *Emoji and aligned columns* |
| CJK and ambiguous-width glyphs | `visual-patterns.md:442` → *Localization › Ambiguous-width characters* |
| Truncating text by cell width | `visual-patterns.md:389` → *Truncation* |
| Width function for your framework | Go `ecosystem-go.md:123`, Rust `ecosystem-rust.md:484`, TS `ecosystem-typescript.md:375` |

## Root rule for the table

**Measure terminal cells, not bytes, code points, `len()` or `.length`.** CJK characters take 2 cells. Emoji take 1 or 2.

- **Go:** `lipgloss.Width()`. It skips ANSI codes and counts wide graphemes.
- **Rust/Ratatui:** `Line::width()` / `Span::width()`. Where the width must match what Ratatui actually draws (e.g. cursor math), use `s.cell_width()` (0.30.1+). `unicode_width` counts halfwidth katakana marks as 0 cells, but the renderer draws 1.
- **TS/Ink:** `string-width`, never `.length`.

Pad and truncate by that measured width. Use the same function everywhere, including headers, the ellipsis and padding.

## Emoji rules

- **Emoji with a Wide base character** (`✅ ❌ ⭐`, most pictographs) are 2 cells in every terminal. These are safe.
- **Emoji built from a narrow base plus a variation selector or joiner** (`⚠️` = U+26A0+U+FE0F, `✔️`, `❤️`, ZWJ families) are 1 or 2 cells depending on the terminal and the width library. Each one can push its row off by a cell.
- **For status columns, use narrow symbols or words:** `✓ ✗ !`. If you do use emoji, pick Wide-base ones, measure them with a grapheme-aware library, and test on the terminals you support.
- **Never let emoji be the only signal.** Some terminals render them as boxes.

## Ambiguous-width rules

This is the usual cause when alignment breaks only for CJK users. Unicode's "ambiguous" class renders 1 cell by default, but 2 when the terminal's ambiguous-wide setting is on. That class includes:
- box drawing and rounded corners
- progress-bar blocks `▏…█`
- `▲▼▶◀`, `● ○ ■ □ ◆ ★`
- `…`, `·`, `•`, `←↑→↓`

If your app and the terminal disagree on a glyph's width, borders and markers drift. go-runewidth treats these as wide under `ja`/`ko`/`zh` locales; most other libraries treat them as narrow.

- Prefer narrow markers: `▸ ▾ ▴ ◉ ◦ ⋅ ✓ ✗ ⋯`.
- Use `▴▾` for sort indicators, not `▲▼`.
- Use `⋅` (U+22C5) as the footer separator, not `·`.
- Reserve 1 cell for the `…` ellipsis and test it with ambiguous-wide on, since it's ambiguous too.
- Keep ASCII borders and an ASCII progress bar one switch away.
- Test with the terminal's ambiguous-wide setting turned on.

## Table layout

- Truncate cells rather than wrapping them.
  - Start or middle truncation for paths.
  - Tail truncation for names and prose.
- Right-align numbers, left-align text.
- Use fixed-width ISO-8601 dates.
- Show full values in a detail view opened with Enter.

## Spinner rules

- **Use Braille frames** `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏` at about 80ms per frame. They're narrow-class, so they're also safe for width.
- **Delay it:** show the spinner only after 100–200ms so instant work doesn't flash it.
- **End on a final state:** `✓` or `✗`, or remove it.
- **No TTY:** suppress it entirely, e.g. in CI logs.
- **Plain, screen-reader or reduced-motion mode:** print one static line (`Working...`), then the result. Don't leave a frozen frame. Give users a named env var to turn it off, as gh does with `GH_SPINNER_DISABLED`.
- **Redraws:** redraw on the spinner tick only. Don't re-render unchanged state in an endless loop, and keep the work itself off the UI thread.
- **Pin its width** so the spinner can't shift the rest of the status bar. A 1-cell Braille frame plus a space is enough.

## Status-line messages

- Start each message with a symbol or word so the meaning survives `NO_COLOR`: `✓ Saved`, `! Low disk`, `✗ Save failed`. Color only reinforces it.
- Clear success and info messages after 3–5 seconds.
- Keep errors until the user dismisses them, and record every message in a log they can reopen.

## Tests

Snapshot rendered frames at 80×24 and 60 columns. Use rows containing CJK, combining marks, both Wide-base and variation-selector emoji, and a truncated cell. Run once with ambiguous-wide on and once under `NO_COLOR`.

If you tell me your framework, I can point to its exact width and truncation helpers and look at your column code.
