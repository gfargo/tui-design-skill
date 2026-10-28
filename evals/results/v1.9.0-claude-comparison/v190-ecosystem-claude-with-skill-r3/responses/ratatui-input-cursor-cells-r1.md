Ratatui hides the real terminal cursor on every frame. It only shows it if you call `frame.set_cursor_position((x, y))` during that same `draw`. That's why a plain `Paragraph` has no cursor.

The Japanese bug is a measurement problem. Your `x` is probably counted in bytes (`String::len()`) or chars. Most Japanese characters are 3 bytes in UTF-8, 1 char, and 2 terminal cells wide, so both counts put the cursor in the wrong place. `x` has to be measured in terminal cells.

## The fix

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

What each part does:

- **Screen coordinates, not widget coordinates.** Start from `inner.x` and `inner.y` (inside the border), not from 0 or `area.x`. Otherwise the cursor sits on the border or one cell off.
- **Measure in cells.** Use `CellWidth::cell_width()` (Ratatui 0.30.1+) on the text *before* the cursor. Prefer it over `Line::width()` or the `unicode-width` crate. Those report zero width for the halfwidth katakana sound marks ﾞ and ﾟ (U+FF9E, U+FF9F), but Ratatui draws each in one cell. With `ｶﾞ`-style input the cursor would drift left. `cell_width()` matches what the renderer actually draws.
- **Store the cursor as a byte offset on a char boundary**, so `text[..cursor]` can't panic. Move it left and right by whole graphemes (the `unicode-segmentation` crate), not by bytes. Then a combining mark or an emoji ZWJ sequence moves as one unit.
- **Clamp to the field.** The `.min(inner.right() - 1)` stops the cursor from leaving the box when the query is longer than the field. For long queries, add horizontal scrolling: keep a scroll offset in cells, render the visible slice, and subtract the offset from `x`.
- **Only while focused.** Call `set_cursor_position` only when the search box has focus. If you don't call it, Ratatui hides the cursor, which is what you want for unfocused fields and list navigation.

## Why use the real cursor instead of drawing one

You could fake a cursor with a reversed-style cell, but the real one is better:

- It follows the user's own cursor shape and blink settings.
- IME candidate windows track it. Japanese input needs this most: if the cursor is wrong, the conversion popup appears in the wrong spot or in the corner.
- Screen readers and magnifiers follow it.

## Lifecycle notes

- Leaving the app with `ratatui::restore()` (or using `ratatui::run`) shows the cursor again on every exit path, including panics, so you don't need to manage that yourself.
- If you change the cursor shape for the input (for example a bar while typing), reset it on exit. Shape isn't part of the default restore.

## Tests worth adding

Render into `TestBackend` at a fixed size and assert the cursor position after typing:

- `日本語`: expect `inner.x + 6`
- `ｶﾞｷﾞ`: expect `inner.x + 4`
- a combining mark such as `é` written as `e` + U+0301
- an emoji
- a query longer than the field, to check the clamp or scrolling

The `CellWidth` details and halfwidth-katakana behavior come from the skill's Ratatui reference (`references/ecosystem-rust.md`, "Text-input cursor" and "Pitfalls" #5). I haven't checked them against your code.
