Render **`Clear` before the dialog**, after drawing the main view. A bordered `Paragraph` leaves unused cells untouched, so underlying text can show through.

For **Ratatui 0.30.1+**, centering and a drop shadow are built in:

```rust
use ratatui::{
    layout::{Constraint, Offset},
    style::Stylize,
    widgets::{Block, Clear, Paragraph, Shadow},
    Frame,
};

fn draw_confirm(frame: &mut Frame) {
    // Call after rendering your main view.
    let area = frame.area().centered(
        Constraint::Percentage(60),
        Constraint::Length(5),
    );

    // Erase underlying text throughout the dialog rectangle.
    frame.render_widget(Clear, area);

    let shadow = Shadow::dark_shade()
        .black()
        .on_dark_gray()
        .offset(Offset::new(2, 1));

    let dialog = Paragraph::new("Continue?\n\n[y] Yes   [Esc] Cancel")
        .white()
        .on_black()
        .block(
            Block::bordered()
                .title("Confirm")
                .shadow(shadow),
        );

    frame.render_widget(dialog, area);
}
```

The draw order is **main view → `Clear` → dialog with shadow**. The shadow paints outside the cleared rectangle; leave room for its two-column, one-row offset.

At 80 columns the dialog is 48 columns wide; at 60 it is 36. Both fit this short prompt:

```text
80-column view                 60-column view
       +Confirm----------+          +Confirm----------+
       |Continue?        |          |Continue?        |
       |                 |          |                 |
       |[y] Yes [Esc] Cancel        |[y] Yes [Esc] Cancel
       +-----------------+##        +-----------------+##
         #################            #################
```

Keep the single border and title; the shadow is optional decoration. While open, route input to the dialog and let `Esc` cancel.

**Version notes:** `Rect::centered` requires 0.30.0+; `Block::shadow` and `Shadow` require 0.30.1+. On older versions, center with nested `Layout` splits and paint an offset shadow rectangle before clearing and rendering the dialog.