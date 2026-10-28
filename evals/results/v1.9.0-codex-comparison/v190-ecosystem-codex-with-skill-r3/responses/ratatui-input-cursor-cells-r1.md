Call **`frame.set_cursor_position((x, y))` on every draw while the search box has focus**. A `Paragraph` renders text but doesn’t request a terminal cursor; Ratatui hides it when no cursor position is set for that frame.

Compute the position using **terminal cell width**, relative to the block’s inner area. Japanese characters commonly occupy two cells, so byte counts and character counts give the wrong offset.

For Ratatui **0.30.1+**, use `CellWidth` to match its renderer:

```rust
use ratatui::{
    buffer::CellWidth,
    layout::Rect,
    widgets::{Block, Paragraph},
    Frame,
};

// Single-line input, without horizontal scrolling.
// cursor_byte must be a valid UTF-8 boundary in text.
fn draw_search(
    frame: &mut Frame,
    area: Rect,
    text: &str,
    cursor_byte: usize,
    focused: bool,
) {
    let block = Block::bordered().title("Search");
    let inner = block.inner(area);

    frame.render_widget(Paragraph::new(text).block(block), area);

    if focused && inner.width > 0 && inner.height > 0 {
        let offset = text[..cursor_byte].cell_width();
        let x = inner.x.saturating_add(offset)
            .min(inner.right() - 1);
        frame.set_cursor_position((x, inner.y));
    }
}
```

For `"日本"` with the caret at the end, the offset is **4 cells**, not 6 bytes or 2 characters.

If the input scrolls horizontally, subtract the scroll offset **in cells** from the prefix width, and scroll the text so the caret stays visible. Clamping alone only keeps the cursor inside the box. Wrapped input also needs the caret’s rendered row and column.

Use the real cursor so the terminal can apply its cursor shape and blink preferences, and IME popups can anchor to its position.