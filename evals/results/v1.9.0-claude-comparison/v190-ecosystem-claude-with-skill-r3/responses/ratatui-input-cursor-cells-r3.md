The fix is to place the real terminal cursor yourself on every draw, and to measure its position in terminal cells rather than bytes or characters. Both of your symptoms come from that.

## Why it goes wrong

1. **No cursor with a bare `Paragraph`.** Ratatui hides the hardware cursor on every frame unless you call `frame.set_cursor_position((x, y))` during that draw. A `Paragraph` only draws text, so it never shows a cursor.
2. **Wrong position after Japanese text.** Most CJK characters take **2 terminal cells**. If you compute `x` from `cursor` (a byte offset), `text.len()`, or `chars().count()`, the result is wrong. For `検索` the byte length is 6, the char count is 2, and the cell width is 4. Only the cell width is correct.

## The pattern

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

What matters here:

- **Screen coordinates, not widget-relative.** Start from `inner.x` and `inner.y`, the area inside the border. Starting from `0` or from `area.x` puts the cursor on top of the border.
- **Measure the prefix before the cursor in cells.** Here that's `text[..cursor].cell_width()`. If you don't have `CellWidth` available, `unicode_width::UnicodeWidthStr::width(&text[..cursor])` gives the same result.
- **Only set it while the input has focus.** When focus moves elsewhere, don't call it and the cursor stays hidden.
- **Set it on every frame.** The position doesn't carry over to the next frame.

## Why use the real cursor instead of a reversed-style cell

The real cursor follows the user's own cursor shape and blink settings. Screen readers also track it. For your Japanese input specifically, **the IME draws its composition text and candidate popup at the hardware cursor**. So once the position is correct, the IME popup also appears next to the text instead of somewhere else on the screen.

## Related bugs to check

- **Cursor movement and editing.** If Left, Right, and Backspace step by one byte or one `char`, they can split a character, or a cluster such as an emoji or a base character plus combining mark. Store `cursor` as a byte offset, but move it by grapheme cluster with `unicode-segmentation`'s `grapheme_indices`. `tui-input` and `ratatui-textarea` already handle this if you'd rather not write it yourself.
- **Text wider than the field.** The `.min(...)` clamp stops the cursor from going past the border, but once the query is longer than the field, the cursor sticks to the right edge. To fix that, keep a horizontal scroll offset measured in cells. Render the visible part with `Paragraph::scroll((0, offset))` and subtract `offset` from `x`. Make sure the offset never lands in the middle of a 2-cell character.
- **Cursor shape.** If you change the shape (for example to a bar in an insert mode) with crossterm's `SetCursorStyle`, set it back to `DefaultUserShape` on every exit path, including panics.

## Test it

Write a frame test at a fixed size using `TestBackend`. Type `検索` and assert the cursor is at `inner.x + 4`. Add cases for a combining mark (`e\u{301}`, 1 cell) and an emoji, and one case where the text is wider than the field.
