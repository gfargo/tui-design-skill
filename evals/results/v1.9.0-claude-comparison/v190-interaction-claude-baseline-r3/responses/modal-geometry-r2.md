The project directory is empty, so this is general guidance rather than advice based on your code.

## Width

Size the dialog to its content, and set a minimum and maximum width:

```
width = clamp(min=36, preferred=content+padding, max=min(64, termCols - 4))
```

- **Maximum about 60–64 columns.** Wider than that, the message lines get too long to read comfortably, and the buttons drift far apart.
- **Minimum about 36 columns.** Below that, a title plus two buttons like `[ Cancel ]  [ Delete ]` starts to feel cramped.
- **Keep at least a 2-column margin on each side** so it's clear the dialog sits on top of other content.
- **Wrap the message** to `width - 4` (border plus 1 space of padding on each side). Don't truncate it. A confirmation that hides its consequence isn't doing its job.
- **Narrow terminals:** if `termCols < min + 4`, use the full width with no side margin. Below about 24 columns, skip the box and show an inline prompt like `Delete 3 files? [y/N]`.
- **Recompute on resize (SIGWINCH).** Don't keep the width you calculated when the dialog opened.
- **Height:** put the dialog about one-third of the way down the screen rather than in the exact center, which tends to look like it sits too low. Keep it short; if the message is long, scroll the body and keep the buttons visible.

## Modals when `NO_COLOR` is set

`NO_COLOR` turns off **color**, not visual structure. Use these instead of color to show the modal:

1. **Borders.** A double-line or heavy border (`╔═╗` / `┏━┓`) separates the modal from the single-line panels behind it.
2. **Opaque fill.** Paint every cell inside the box with spaces so the content behind it doesn't show through. This is what makes it look like a layer.
3. **Background.** You can't dim it without color. Either leave it as is (the border and fill are enough) or replace it with a light shade character (`░`) if you want a strong "background is inactive" cue.
4. **Focus shown in text.** Don't rely on highlighting alone:
   ```
   ╔══════════ Delete files? ══════════╗
   ║                                   ║
   ║  3 files will be permanently      ║
   ║  removed. This can't be undone.   ║
   ║                                   ║
   ║        [ Cancel ]   > Delete <    ║
   ║                                   ║
   ╚═══════════════════════════════════╝
   ```
   Brackets or `> <` markers on the focused button work in every terminal, with screen readers, and over copy/paste.
5. **Attributes are fine.** Bold, underline and reverse video aren't colors, so they're generally acceptable under `NO_COLOR`. Using **reverse** on the focused button is a common choice. Still keep the text markers, because `TERM=dumb` and some pipes drop attributes too.
6. **ASCII fallback.** If the locale isn't UTF-8 or `TERM=dumb`, draw the border with `+`, `-`, `=` and `|`.
7. **Make the default safe.** Focus Cancel first for destructive actions, and show the keys (`Enter` to confirm, `Esc` to cancel) in the footer or the button labels.

Check `NO_COLOR` as "set and non-empty" (`os.Getenv("NO_COLOR") != ""`). Also let a `--color=always` flag override it, since that's what the spec recommends.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink, etc.), I can show how this maps to its styling and layout APIs.
