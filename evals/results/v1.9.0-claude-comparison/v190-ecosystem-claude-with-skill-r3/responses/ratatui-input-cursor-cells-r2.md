You have two separate bugs. Ratatui hides the real cursor by default, and your x position is counted in bytes or chars when it should be counted in terminal cells.

## Why there's no cursor

Ratatui hides the terminal cursor on every frame unless you place it during that draw. Rendering a `Paragraph` only paints cells and never shows a cursor. Call `frame.set_cursor_position((x, y))` inside the same `draw` closure, and only while the search box has focus.

Use the real cursor rather than a reverse-video cell. It respects the user's cursor shape and blink settings, and IME candidate popups and screen readers follow it. With a Japanese IME, the uncommitted text (preedit) is drawn wherever the real cursor sits, so a wrong position also puts the candidate window in the wrong place.

## Why it's in the wrong place after Japanese text

Most Japanese characters are 2 cells wide. If x comes from `text.len()` (bytes, 3 per kana) or `text.chars().count()` (1 per character), the cursor lands too far right or too far left. Measure the width of the text before the cursor in cells. Also, x is in screen coordinates, so start from the inner area of the block, not 0.

```rust
use ratatui::{buffer::CellWidth, layout::Rect, widgets::{Block, Paragraph}, Frame};

/// `cursor` is a byte offset on a char boundary of `text`.
fn draw_input(frame: &mut Frame, area: Rect, text: &str, cursor: usize, focused: bool) {
    let block = Block::bordered().title("Search");
    let inner = block.inner(area);
    frame.render_widget(Paragraph::new(text).block(block), area);

    if focused {
        let x = (inner.x + text[..cursor].cell_width())
            .min(inner.right().saturating_sub(1));
        frame.set_cursor_position((x, inner.y));
    }
}
```

- **Keep the cursor as a byte offset.** That lets you slice with `text[..cursor]`. Move it left and right by grapheme cluster, not by byte, so it never lands inside a character. The `unicode-segmentation` crate does this.
- **Use `CellWidth::cell_width()`** (Ratatui 0.30.1+) rather than `Line::width()` or `unicode_width` for cursor math. It matches what Ratatui's renderer actually draws. The others count the halfwidth katakana sound marks ﾞ and ﾟ (U+FF9E/U+FF9F) as 0 cells, but the renderer draws them as 1, so the cursor drifts after text like `ｶﾞ`. On an older Ratatui, `unicode_width` gives the same result as `cell_width` except for those marks.
- **The `.min(...)` clamp only keeps the cursor inside the box.** If the query can be wider than the field, scroll the visible part horizontally instead of letting the cursor stick at the right edge. Keep a cell offset, render with `Paragraph::scroll((0, offset))`, and subtract `offset` from x.

## Test it

Unit-test the x calculation with ASCII, `日本語`, mixed `abc日本`, halfwidth `ｶﾞ`, and an emoji or a character with a combining mark. Then type with a real IME in your target terminal and check that the candidate window appears at the cursor. Emoji sequences can still be measured differently by the app and the terminal, depending on the terminal.
