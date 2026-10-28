Position the cursor in **terminal cells**, not UTF-8 bytes or character counts. Japanese characters typically occupy two cells. Also, `Paragraph` only draws text; it doesn’t position the terminal cursor.

Call `Frame::set_cursor_position` on **every draw** where the input is focused:

```rust
use ratatui::widgets::{Block, Borders, Paragraph};
use unicode_width::UnicodeWidthStr; // add unicode-width to Cargo.toml

terminal.draw(|frame| {
    let block = Block::default().borders(Borders::ALL);
    let inner = block.inner(search_area);

    frame.render_widget(
        Paragraph::new(input.as_str()).block(block),
        search_area,
    );

    // cursor_byte must be a valid UTF-8 boundary.
    // For a cursor at the end, use input.len().
    let column = input[..cursor_byte].width();

    if focused && inner.height > 0 && column < usize::from(inner.width) {
        frame.set_cursor_position((
            inner.x + column as u16,
            inner.y,
        ));
    }
})?;
```

For `"日本"`, `.len()` is 6 bytes, `.chars().count()` is 2, and `.width()` is **4 terminal cells**.

`block.inner(...)` accounts for borders and padding. If you scroll horizontally, subtract the scroll offset in cells from the cursor column; if you wrap text, calculate the rendered row and column too. Keep the cursor inside the visible content area, scrolling when necessary.

Ratatui shows the cursor when you set its position and hides it on frames where you don’t. Older versions use `frame.set_cursor(x, y)` instead. Blinking and cursor shape are separate terminal settings.