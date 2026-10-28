`Paragraph` only renders text; it doesn’t place the real terminal cursor. Set its position on the `Frame` **on every draw while the input is focused**.

Coordinates are terminal cells, so use Unicode display width—not `String::len()` (bytes) or `.chars().count()`.

```rust
use ratatui::widgets::{Block, Paragraph};
use unicode_width::UnicodeWidthStr;

terminal.draw(|frame| {
    let block = Block::bordered().title("Search");
    let inner = block.inner(search_area);

    frame.render_widget(
        Paragraph::new(input.as_str()).block(block),
        search_area,
    );

    // Cursor at the end of an unscrolled, single-line input.
    let column = input.as_str().width();

    if focused && inner.height > 0 && column < usize::from(inner.width) {
        frame.set_cursor_position((
            inner.x + column as u16,
            inner.y,
        ));
    }
})?;
```

Add `unicode-width` as a direct dependency. For example, `"日本"` usually occupies **4 terminal columns**, despite having 2 characters and 6 UTF-8 bytes.

If the cursor can move within the text, measure the **prefix before the cursor**:

```rust
let column = input[..cursor_byte_index].width();
```

Ensure that index is a valid UTF-8 boundary; editing movement should generally follow grapheme boundaries.

For horizontal scrolling, subtract the scroll offset **in display cells**, and only place the cursor if it’s visible. Borders, padding, alignment, and wrapping must also be reflected in the coordinates; `block.inner(...)` handles the block’s borders and padding.

Current Ratatui uses `frame.set_cursor_position((x, y))`; older versions use `frame.set_cursor(x, y)`. Calling it requests a visible cursor for that frame; its blinking style is controlled separately by the terminal/backend.