Your workspace doesn't have any Rust files, so here's a general answer you can adapt.

## Why the text shows through

Ratatui uses immediate-mode rendering. Every widget writes into one shared buffer, and a widget only changes the cells it actually draws. A `Paragraph` with a `Block` draws the border and the text, but it leaves the blank cells inside unchanged. Whatever the main view drew there stays visible.

To fix it, render the `Clear` widget over the popup area first. `Clear` resets every cell in that area. Then render the dialog on top.

## Centering

`Layout` with `Flex::Center` does this cleanly. It needs ratatui 0.26 or later.

```rust
use ratatui::{
    layout::{Constraint, Flex, Layout, Rect},
    style::{Color, Style, Stylize},
    text::Line,
    widgets::{Block, BorderType, Clear, Paragraph, Wrap},
    Frame,
};

fn centered_rect(area: Rect, width: u16, height: u16) -> Rect {
    let [area] = Layout::horizontal([Constraint::Length(width)])
        .flex(Flex::Center)
        .areas(area);
    let [area] = Layout::vertical([Constraint::Length(height)])
        .flex(Flex::Center)
        .areas(area);
    area
}
```

`Constraint::Length` gives the dialog a fixed size. For a size relative to the screen, use `Constraint::Percentage(50)` instead. If the terminal is smaller than the requested size, the layout shrinks the dialog to fit.

## Drop shadow

There's no built-in shadow, but you can make one by restyling the cells in a rectangle offset down and to the right of the dialog. Offsetting by **2 columns and 1 row** looks more even than 1×1, because terminal cells are about twice as tall as they are wide.

```rust
fn render_shadow(frame: &mut Frame, popup: Rect) {
    let shadow = Rect {
        x: popup.x.saturating_add(2),
        y: popup.y.saturating_add(1),
        ..popup
    }
    .intersection(frame.area()); // don't write past the screen edge

    let buf = frame.buffer_mut();
    for y in shadow.top()..shadow.bottom() {
        for x in shadow.left()..shadow.right() {
            if let Some(cell) = buf.cell_mut((x, y)) {
                // Dim what's underneath, so it looks like a translucent shadow
                cell.set_fg(Color::DarkGray).set_bg(Color::Black);
            }
        }
    }
}
```

This dims the existing characters, so the content underneath stays faintly visible. For a solid shadow, render `Block::new().style(Style::new().bg(Color::Black))` over the shadow rectangle instead.

## Putting it together

Draw order matters: main view, then shadow, then `Clear`, then the dialog. The dialog covers the part of the shadow that overlaps it, so only the offset edge remains visible.

```rust
fn render_confirm(frame: &mut Frame, message: &str) {
    let popup = centered_rect(frame.area(), 40, 7);

    render_shadow(frame, popup);
    frame.render_widget(Clear, popup); // wipe what's underneath

    let block = Block::bordered()
        .border_type(BorderType::Rounded)
        .title(" Confirm ")
        .title_bottom(Line::from(" [y]es / [n]o ").centered())
        // Clear resets cells to the terminal's default background.
        // Set a bg here if you want the dialog to be a distinct color.
        .style(Style::new().bg(Color::Rgb(30, 30, 46)));

    let dialog = Paragraph::new(message)
        .block(block)
        .centered()
        .wrap(Wrap { trim: true });

    frame.render_widget(dialog, popup);
}

// In your draw closure:
// render_main(frame);
// if app.confirming { render_confirm(frame, "Delete this item?"); }
```

**Version notes:**
- `frame.area()` replaced `frame.size()` in 0.28.
- `buf.cell_mut((x, y))` is 0.28 and later. On older versions, use `buf.get_mut(x, y)`.
- `Paragraph::centered()` and `Line::centered()` are 0.26 and later. On older versions, use `.alignment(Alignment::Center)`.
- On ratatui 0.30, `area.centered(Constraint::Length(40), Constraint::Length(7))` can replace the `centered_rect` helper.
