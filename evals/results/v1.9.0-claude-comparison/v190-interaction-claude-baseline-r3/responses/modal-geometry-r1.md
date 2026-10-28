The working directory is empty, so this is general guidance rather than advice tied to your code.

## Dialog width

**Size it to the content, then clamp it to the terminal:**

```
width = clamp(content_width + padding, min=40, max=min(60, term_cols - 4))
```

- **Aim for 40–60 columns.** A confirmation is a short question plus 2–3 buttons. Wider than about 60 columns makes the text hard to scan, and the dialog stops looking like a modal.
- **Minimum of about 40 columns** so a prompt like "Delete 3 files? [y/N]" and its buttons fit on one line without cramming.
- **Keep a margin of at least 2 columns on each side**, so the dialog never touches the terminal edges. With no gap on either side it looks like part of the screen, not a layer on top of it.
- **Wrap long messages** at the inner width and let the dialog grow taller, not wider. Put long details like file paths in a scrollable body or truncate them in the middle (`/very/long/…/file.txt`).
- **Small terminals:** if `term_cols < 44` or so, make the dialog full width with no border, or fall back to an inline prompt on the last line. Don't render a broken box.
- **Center it** horizontally and a little above vertical center. That reads better than exact center.
- **Recompute on resize** (SIGWINCH). Don't cache the width.

## Modals under NO_COLOR

[NO_COLOR](https://no-color.org) means no **color**. It doesn't mean no styling, so you still have everything else:

1. **Box-drawing borders do most of the work.** Use a heavier or double border for the modal than for normal panels so it stands out without color:
   ```
   ╔══════════════ Confirm ══════════════╗
   ║                                     ║
   ║  Delete 3 files? This can't be      ║
   ║  undone.                            ║
   ║                                     ║
   ║          [ Cancel ]  < Delete >     ║
   ╚═════════════════════════════════════╝
   ```
2. **Clear the area behind the dialog.** Fill the box interior with spaces so text underneath doesn't show through. Many toolkits paint over cells without clearing them.
3. **Use SGR attributes, which aren't colors:** **bold** for the title, **reverse video** (`\e[7m`) for the focused button, and optionally dim (`\e[2m`) for the background content. All of these are allowed under NO_COLOR.
4. **Mark focus with text as well.** Use brackets or arrows (`> Delete <`, `[*Delete*]`) so focus is still visible if reverse video doesn't render, for example in screen readers, logs, or `TERM=dumb`.
5. **Optionally add a drop shadow** with `░` or `▒` one cell to the right and below the box. This gives depth without color.
6. **Fall back further for `TERM=dumb` or non-UTF-8 locales:** use ASCII borders (`+--+`, `|`), and if stdout isn't a TTY, skip the modal and print a plain prompt (`Delete 3 files? [y/N] `).

**Implementation tip:** route all styling through one theme object and check `NO_COLOR` once. Check that it's set and non-empty, as the spec says. Then swap in a monochrome theme that keeps attributes and borders but drops the colors. Don't scatter `if no_color` checks through your rendering code.

If you tell me your framework (Bubble Tea/Lip Gloss, Ratatui, Textual, Ink, etc.), I can show the exact code for this.
