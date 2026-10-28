Position the real cursor with **`Frame::set_cursor_position` on every draw**. A `Paragraph` only renders text; it doesn’t request a terminal cursor.

Cursor coordinates are **terminal cells**, not UTF-8 bytes or character counts. Japanese characters commonly occupy two cells. Use `unicode-width` to measure the text before the editing cursor:

```rust
use ratatui::widgets::{Block, Paragraph};
use unicode_width::UnicodeWidthStr;

terminal.draw(|frame| {
    let block = Block::bordered().title("Search");
    let inner = block.inner(area);

    frame.render_widget(
        Paragraph::new(input.as_str()).block(block),
        area,
    );

    // cursor_byte is a valid UTF-8 boundary in input.
    // For an input whose cursor is always at the end, use input.len().
    let prefix = &input[..cursor_byte];
    let column = UnicodeWidthStr::width(prefix);

    if focused && inner.height > 0 && column < usize::from(inner.width) {
        frame.set_cursor_position((
            inner.x + column as u16,
            inner.y,
        ));
    }
})?;
```

For `"日本"`, the cursor offset is **4 cells**, whereas `.len()` returns 6 bytes and `.chars().count()` returns 2 characters.

The block’s `inner` rectangle accounts for borders and padding. If you scroll horizontally, subtract the scroll offset **in cells**; if you wrap text, also calculate the cursor’s displayed row. Keep the resulting position inside the visible content area.

Ratatui shows the cursor when you call `set_cursor_position` and hides it for frames where you don’t. The terminal controls its blinking appearance. Older Ratatui versions call this method `frame.set_cursor(x, y)`.