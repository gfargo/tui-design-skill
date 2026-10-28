To fix it, render `Clear` into the popup rect before you draw the dialog. To center it, use `Rect::centered`. For the shadow, use `Block::shadow`. `Rect::centered` needs Ratatui 0.30.0 or later, and `Block::shadow` needs 0.30.1 or later.

### Why the text shows through
In Ratatui, every widget writes into the same buffer. A `Paragraph` only overwrites the cells it actually draws, so any cell your text doesn't reach keeps the main view's content from earlier in the frame. `Clear` resets every cell in the rect first, so the dialog starts from a blank area.

### Ratatui 0.30.1+
```rust
use ratatui::layout::{Constraint, Offset};
use ratatui::widgets::{Block, Clear, Paragraph, Shadow};
use ratatui::{style::Stylize, Frame};

fn draw_confirm(frame: &mut Frame, message: &str) {
    // Draw the main view first, then this, in the same draw call.
    let area = frame.area().centered(Constraint::Percentage(60), Constraint::Length(5));
    frame.render_widget(Clear, area); // blank the cells under the dialog
    let shadow = Shadow::dark_shade().black().on_dark_gray().offset(Offset::new(2, 1));
    let block = Block::bordered().title(" Delete 3 files? ").shadow(shadow);
    frame.render_widget(Paragraph::new(message).block(block), area);
}
```

The shadow is drawn on the cells beside and below the block, outside the rect you cleared, so `Clear` doesn't erase it. An offset of `(2, 1)` looks even because terminal cells are about twice as tall as they are wide.

### On an older Ratatui
Center the rect with a `Flex::Center` layout, and draw the shadow yourself by restyling the shifted rect. Do this before `Clear`:

```rust
use ratatui::layout::{Constraint, Flex, Layout, Offset, Rect};
use ratatui::style::{Color, Style};

fn centered(area: Rect, w: Constraint, h: Constraint) -> Rect {
    let [area] = Layout::horizontal([w]).flex(Flex::Center).areas(area);
    let [area] = Layout::vertical([h]).flex(Flex::Center).areas(area);
    area
}

// in draw:
let area = centered(frame.area(), Constraint::Percentage(60), Constraint::Length(5));
let shadow = area.offset(Offset { x: 2, y: 1 }).intersection(frame.area());
frame.buffer_mut().set_style(shadow, Style::new().fg(Color::DarkGray).bg(Color::Black));
frame.render_widget(Clear, area);
frame.render_widget(Paragraph::new(message).block(block), area);
```

The `set_style` call keeps the characters underneath and only darkens them, which reads as a shadow. The dialog then covers everything except the offset L-shape. The `intersection` stops the shadow from running past the screen edge.

### Design notes for a confirm dialog
- **Size:** 60–80% of the terminal width, at most about 80 columns, at least 30. Placing it slightly above vertical center often looks better than exact center. At a 60-column split, 60% is only 36 columns, so make the minimum something like `Constraint::Min(30)` with a cap, or long messages will wrap badly.
- **Don't rely on the shadow or dimming alone:** they depend on color, and the faint attribute is ignored by some terminals and under `NO_COLOR`. The border, a title that asks the question, and footer hints changed to something like `y delete ⋅ n/esc cancel` are what tell the user they're in a dialog.
- **Default to No:** use `[y/N]`, so pressing Enter doesn't confirm a destructive action. Esc should close only the dialog, and the dialog should take all key input while it's open.
- **Draw it every frame:** keep a "dialog open" flag in your app state and draw the dialog whenever it's set, in the same `terminal.draw` call after the main view. If you draw it only once, the next redraw erases it.
