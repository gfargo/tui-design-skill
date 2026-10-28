No Rust files turned up in the working directory, so this answer is general rather than a fix to your code. These are two separate problems.

## 1. No cursor with a `Paragraph`

Widgets never draw a cursor. On every `terminal.draw(...)`, Ratatui hides the real terminal cursor unless you place it yourself during that frame:

```rust
frame.set_cursor_position(Position::new(x, y)); // ratatui ≥ 0.28
// older versions: frame.set_cursor(x, y);
```

Call this on **every frame** in which the search box has focus. If you skip it for a frame, the cursor is hidden again.

## 2. Wrong position after typing Japanese

You're probably calculating the column from `text.len()` (bytes) or `text.chars().count()` (characters). The terminal needs **display columns**. Most Japanese characters are 2 columns wide, and a character like `あ` is 3 bytes long. Use `unicode-width` to get the column, and `unicode-segmentation` to move the cursor one grapheme at a time:

```rust
use ratatui::{prelude::*, widgets::{Block, Paragraph}};
use unicode_segmentation::UnicodeSegmentation;
use unicode_width::UnicodeWidthStr;

struct SearchBox {
    text: String,
    cursor: usize, // byte index, always on a grapheme boundary
}

impl SearchBox {
    fn insert(&mut self, c: char) {
        self.text.insert(self.cursor, c);
        self.cursor += c.len_utf8();
    }
    fn left(&mut self) {
        if let Some((i, _)) = self.text[..self.cursor].grapheme_indices(true).next_back() {
            self.cursor = i;
        }
    }
    fn right(&mut self) {
        if let Some(g) = self.text[self.cursor..].graphemes(true).next() {
            self.cursor += g.len();
        }
    }
    fn backspace(&mut self) {
        let end = self.cursor;
        self.left();
        self.text.replace_range(self.cursor..end, "");
    }

    fn render(&self, frame: &mut Frame, area: Rect, focused: bool) {
        let block = Block::bordered().title("Search");
        let inner = block.inner(area); // accounts for borders/padding

        // Display width of everything before the cursor
        let cursor_col = self.text[..self.cursor].width() as u16;
        // Scroll horizontally so the cursor stays visible
        let scroll = cursor_col.saturating_sub(inner.width.saturating_sub(1));

        frame.render_widget(
            Paragraph::new(self.text.as_str()).scroll((0, scroll)).block(block),
            area,
        );

        if focused {
            frame.set_cursor_position(Position::new(
                inner.x + cursor_col - scroll,
                inner.y,
            ));
        }
    }
}
```

## Details that matter

- **IME input:** the terminal draws the IME's in-progress text (preedit) and candidate window at the real cursor. Putting the cursor in the right place therefore fixes where the IME popup appears too.
- **Borders:** take the position from `block.inner(area)`, not `area`. Otherwise the cursor sits one cell off, on the border.
- **Cursor shape and blinking:** the default shape depends on the terminal. To control it, use crossterm: `execute!(stdout(), SetCursorStyle::BlinkingBar)`. On exit, restore it with `SetCursorStyle::DefaultUserShape`.
- **Ambiguous-width characters:** some symbols, like `○` and `①`, show as 1 or 2 columns depending on the terminal's settings. `unicode-width` treats them as 1 column, so the cursor can still be off for those. Ordinary kana and kanji are reliably 2 columns.
- **Horizontal scrolling:** if a 2-column character crosses the left edge of the visible area, the layout can be off by one. If that matters, scroll by whole graphemes instead of raw columns.

If you'd rather not handle this yourself, the `tui-input` and `tui-textarea` crates do the width and grapheme handling and give you the cursor position to pass to `set_cursor_position`.
