Call **`frame.set_cursor_position((x, y))` on every draw while the search input has focus**. Rendering a `Paragraph` only paints text; Ratatui hides the real cursor unless you explicitly position it.

Coordinates are **absolute screen cells**, measured from the input’s inner area. Japanese characters commonly occupy two cells, so neither `text.len()` nor `text.chars().count()` gives the correct offset.

For Ratatui **0.30.1+**:

```rust
use ratatui::{
    buffer::CellWidth,
    layout::Rect,
    widgets::{Block, Paragraph},
    Frame,
};

// Single-line, left-aligned input without scrolling.
// `cursor_byte` must be a valid UTF-8 boundary in `text`.
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

Use **`CellWidth` to match Ratatui’s rendering**, including Japanese halfwidth katakana marks that other width calculations can mismeasure.

For a scrolling input, subtract the horizontal scroll offset **in cells** and scroll enough to keep the insertion point visible; the clamp above only keeps the cursor inside the box. For wrapping or multiline input, calculate the rendered row as well. Keep editing positions at grapheme boundaries so movement doesn’t split combining sequences.

Using the real cursor preserves terminal blink/shape preferences and gives IME candidate windows the correct anchor.