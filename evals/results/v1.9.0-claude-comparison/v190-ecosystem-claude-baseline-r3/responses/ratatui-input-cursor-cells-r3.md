I didn't find any Rust files in the working directory, so this is a general answer rather than a fix to your code. You have two separate problems.

## 1. No cursor with a plain `Paragraph`

That's expected. Widgets only write cells into the buffer. They never move the terminal cursor. After each `terminal.draw(...)`, Ratatui **hides** the cursor unless you set a position during that frame. You have to set it yourself, inside the draw closure, on every frame:

```rust
frame.set_cursor_position(Position::new(x, y)); // ratatui ≥ 0.28
// older versions: frame.set_cursor(x, y);
```

Only call it when the search box has focus. If you don't call it, the cursor is hidden, which is what you want for unfocused inputs.

## 2. Cursor in the wrong place after Japanese text

You're almost certainly computing the column from `input.len()` (bytes) or `input.chars().count()` (code points). The terminal needs **display width**:

| | `"検索"` |
|---|---|
| `.len()` (bytes) | 6 |
| `.chars().count()` | 2 |
| display columns | **4** ← what you need |

Most CJK characters take 2 columns. Use the `unicode-width` crate, which Ratatui already depends on. Also measure only the text *before* the cursor, not the whole string, so the cursor stays right when it's in the middle of the text.

## Putting it together

```toml
unicode-width = "0.2"
unicode-segmentation = "1"
```

```rust
use ratatui::{prelude::*, widgets::{Block, Paragraph}};
use unicode_segmentation::UnicodeSegmentation;
use unicode_width::UnicodeWidthStr;

struct SearchBox {
    input: String,
    /// Byte index into `input`, always on a grapheme boundary.
    cursor: usize,
}

impl SearchBox {
    fn insert(&mut self, c: char) {
        self.input.insert(self.cursor, c);
        self.cursor += c.len_utf8();
    }

    fn prev_boundary(&self) -> Option<usize> {
        self.input[..self.cursor].grapheme_indices(true).next_back().map(|(i, _)| i)
    }

    fn move_left(&mut self) {
        if let Some(i) = self.prev_boundary() { self.cursor = i; }
    }

    fn move_right(&mut self) {
        if let Some(g) = self.input[self.cursor..].graphemes(true).next() {
            self.cursor += g.len();
        }
    }

    fn backspace(&mut self) {
        if let Some(i) = self.prev_boundary() {
            self.input.replace_range(i..self.cursor, "");
            self.cursor = i;
        }
    }

    fn render(&self, frame: &mut Frame, area: Rect, focused: bool) {
        let block = Block::bordered().title("Search");
        let inner = block.inner(area); // accounts for borders/padding

        // Display columns before the cursor, not bytes or chars.
        let cursor_col = self.input[..self.cursor].width() as u16;

        // Scroll horizontally so the cursor stays visible.
        let scroll_x = cursor_col.saturating_sub(inner.width.saturating_sub(1));

        frame.render_widget(
            Paragraph::new(self.input.as_str()).scroll((0, scroll_x)).block(block),
            area,
        );

        if focused {
            frame.set_cursor_position(Position::new(
                inner.x + cursor_col - scroll_x,
                inner.y,
            ));
        }
    }
}
```

## Details that cause problems later

- **Store the cursor as a byte index on grapheme boundaries**, not a char count. Then slicing (`&input[..cursor]`) is cheap and can't panic. Moving by grapheme means `が` written as か + a combining mark, or an emoji with modifiers, moves as one unit.
- **Offset from the inner area.** Use `block.inner(area)` so borders and padding are included in the position. A bare `area.x + col` is off by one when there's a border.
- **This also fixes the IME.** While you're composing Japanese text, macOS and other IMEs draw the preedit text and candidate window at the real terminal cursor. A correctly placed cursor puts the composition popup in the right spot, not in a corner of the screen.
- **Ambiguous-width characters** (some symbols like `○` or `※`) are 1 column in most terminals and 2 in some CJK-locale setups. `.width()` assumes 1. If you see drift on those characters specifically, that's the reason, and `width_cjk()` is the alternative.
- **Cursor shape:** if you want a bar instead of a block, run crossterm's `execute!(stdout, SetCursorStyle::SteadyBar)` once at startup and reset it on exit.

If you paste your current input-handling and render code, I can show exactly where the column calculation goes wrong.
