Call **`frame.set_cursor_position((x, y))` on every draw while the search box has focus**. Rendering a `Paragraph` paints text; it does not request a visible terminal cursor.

Compute the cursor’s offset using **terminal cells**, not UTF-8 bytes or character counts. For Ratatui **0.30.1+**, use `CellWidth` to match its renderer:

```rust
use ratatui::{
    buffer::CellWidth,
    layout::Rect,
    widgets::{Block, Paragraph},
    Frame,
};

// Single-line, left-aligned input without horizontal scrolling.
// cursor_byte must be a valid UTF-8 boundary, ideally a grapheme boundary.
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
        let x = inner.x
            .saturating_add(offset)
            .min(inner.right() - 1);

        frame.set_cursor_position((x, inner.y));
    }
}
```

For `"日本"`, the end cursor is **four cells** from the content origin, although the string contains two characters and six UTF-8 bytes.

Key details:

- Use absolute screen coordinates: start at `block.inner(area)` to account for borders and padding.
- For horizontal scrolling, subtract the scroll offset **in cells**, and scroll the rendered text consistently so the insertion point stays visible. Clamping alone does not implement scrolling.
- When focus leaves the input, omit `set_cursor_position`; Ratatui hides the cursor for that frame.
- Use the real cursor so terminal blink settings and IME popup positioning can follow it. A painted block character cannot provide that behavior.

Check Japanese, halfwidth katakana marks, combining marks, emoji, and an input narrower than its text.