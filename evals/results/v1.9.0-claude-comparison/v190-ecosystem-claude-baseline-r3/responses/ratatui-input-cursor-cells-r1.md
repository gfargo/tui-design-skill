There's no project code in this directory, so here's the general fix. There are two separate problems.

## 1. Why a Paragraph shows no cursor

Ratatui hides the terminal cursor on every `draw()` unless you place it during that frame. Widgets like `Paragraph` never place it. Call `set_cursor_position` inside the draw closure on every frame where the search box has focus:

```rust
frame.set_cursor_position((x, y)); // ratatui ≥ 0.28 (older: frame.set_cursor(x, y))
```

If you skip the call in a frame, the cursor is hidden for that frame. That's also how you hide it when the box loses focus.

## 2. Why it's in the wrong place after Japanese text

The cursor's x position needs to be in **terminal columns**, but you're probably calculating it in a different unit:

| Calculation | `"検索"` gives | Correct? |
|---|---|---|
| `s.len()` (bytes) | 6 | ✗ (too far right) |
| `s.chars().count()` | 2 | ✗ (too far left) |
| `s.width()` (display columns) | 4 | ✓ |

Most CJK characters take up 2 columns. Use the `unicode-width` crate, which Ratatui already uses internally to lay out text, so your cursor will match what was drawn.

## A working pattern

```rust
use ratatui::{prelude::*, widgets::{Block, Paragraph}};
use unicode_width::UnicodeWidthStr;

struct SearchBox {
    input: String,
    cursor: usize, // byte index into `input`, always on a char boundary
    focused: bool,
}

fn render_search(frame: &mut Frame, area: Rect, sb: &SearchBox) {
    let block = Block::bordered().title("Search");
    let inner = block.inner(area); // accounts for borders/padding

    // Display width of the text *before* the cursor
    let cursor_col = sb.input[..sb.cursor].width() as u16;

    // Scroll horizontally so the cursor stays visible
    let scroll = cursor_col.saturating_sub(inner.width.saturating_sub(1));

    frame.render_widget(
        Paragraph::new(sb.input.as_str()).scroll((0, scroll)).block(block),
        area,
    );

    if sb.focused {
        frame.set_cursor_position((inner.x + cursor_col - scroll, inner.y));
    }
}
```

## Editing operations that keep `cursor` valid

```rust
// insert
sb.input.insert(sb.cursor, c);
sb.cursor += c.len_utf8();

// move left / right by grapheme (unicode-segmentation crate)
use unicode_segmentation::UnicodeSegmentation;
let left = sb.input[..sb.cursor].grapheme_indices(true).next_back().map_or(0, |(i, _)| i);
let right = sb.input[sb.cursor..].graphemes(true).next().map_or(sb.cursor, |g| sb.cursor + g.len());
```

Store the cursor as a **byte index** and compute the column at render time. Don't store a column number and try to keep it in sync. Moving by grapheme instead of by `char` also handles combining marks and emoji with ZWJ correctly.

## Other notes

- **IME:** Japanese input methods draw the composition text and candidate window at the real terminal cursor. Placing the cursor correctly fixes where the IME popup appears too.
- **Cursor shape:** for an "I-beam" cursor, run `crossterm::execute!(stdout, SetCursorStyle::BlinkingBar)` once at startup, and reset it to `DefaultUserShape` on exit.
- **Ambiguous-width characters** (some symbols like `○` or `※`) may render as 1 or 2 columns depending on the terminal or locale. `unicode-width` treats them as 1. If a few symbols are slightly off, that's the cause, not your math.
- If you're also using `tui-textarea` or `tui-input`, those crates already handle the width calculation. With `tui-input`, use `input.visual_cursor()` for the column.
