The working directory is empty, so this is general guidance rather than advice tied to your code. If you share the framework you're using (Bubble Tea, Ratatui, Textual, Ink, etc.), I can make it concrete.

## Dialog width

**Size it to the content, then clamp it to the terminal:**

```
width = clamp(content_width + padding*2 + border*2,
              min = 30,
              max = min(60, term_cols - 4))
```

- **Aim for about 40–60 columns.** A confirmation is a short question plus 2–3 buttons. Lines wider than about 60 columns are harder to read, and very wide dialogs look like full screens instead of interruptions.
- **Minimum of about 30 columns.** Below that, a button row like `[ Cancel ]  [ Delete ]` gets cramped.
- **Leave at least 2 columns of margin on each side** so it's clear the dialog sits on top of the screen behind it.
- **Wrap the message text to the inner width.** Don't widen the dialog to fit a long filename. Truncate long paths in the middle (`~/projects/…/config.yaml`).
- **In narrow terminals (< ~34 cols), go full-width** with no side margin rather than failing to render. Also handle resize events by recomputing the width and re-wrapping the text.
- **Calculate height from the wrapped text** and center the dialog vertically. Optionally bias it slightly above center, which tends to look better.
- **Measure display width, not string length.** CJK characters and emoji take 2 cells. Use `wcwidth` / `unicode-width` / `go-runewidth` or your framework's equivalent.

## Modals under `NO_COLOR`

`NO_COLOR` only means "don't emit color." Bold, reverse video, underline and box-drawing characters are still allowed. So the modal needs to read as a modal through structure, not hue:

1. **Draw a border with box-drawing characters.** This does most of the work. A heavier or double border (`╔═╗`) helps it stand out from any single-line panels behind it.
   ```
   ╔══════════ Delete file? ══════════╗
   ║                                  ║
   ║  This will permanently delete    ║
   ║  report-final.pdf.               ║
   ║                                  ║
   ║        [ Cancel ]  [▸Delete◂]    ║
   ╚══════════════════════════════════╝
   ```
2. **Clear the dialog's area completely**, filling it with spaces, so no background text shows through. This replaces the colored background you'd normally use.
3. **Show focus with reverse video (SGR 7) or bold**, plus a non-styling cue such as `▸ ◂`, `> <` or `[*]`. Then focus is still visible even if styles get stripped as well.
4. **Optionally dim the background.** SGR 2 (faint) on the content behind the dialog works in many terminals, but not all, so don't rely on it alone.
5. **Put the title in the top border** and keep the key hints as text (`Enter confirm · Esc cancel`). Don't communicate anything through color alone, such as a red "Delete" button. Use wording like `Delete (permanent)` or a `⚠` marker instead.
6. **Add an ASCII fallback** (`+--+`, `|`) for when the locale isn't UTF-8 or the user asks for it. Some setups that use `NO_COLOR` also have limited glyph support.

Implementation note: check `NO_COLOR` once at startup (it counts as set if present and non-empty) and route all styling through a theme object. The modal component then asks the theme for "focused button style" and "border style," and doesn't need to know which mode it's in.
