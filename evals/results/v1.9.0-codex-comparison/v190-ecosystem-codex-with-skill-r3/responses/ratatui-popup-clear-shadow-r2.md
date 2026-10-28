Render **the main view → `Clear` → the dialog**, in that order. A bordered `Paragraph` leaves some cells untouched, so underlying text survives unless you clear the popup rectangle first.

For **Ratatui 0.30.1+**, centering and a drop shadow are built in:

```rust
use ratatui::{
    layout::{Constraint, Offset},
    style::Stylize,
    widgets::{Block, Clear, Paragraph, Shadow},
    Frame,
};

fn draw_confirm(frame: &mut Frame) {
    // Draw your main view before calling this function.
    let area = frame.area().centered(
        Constraint::Percentage(60),
        Constraint::Length(5),
    );

    frame.render_widget(Clear, area);

    let shadow = Shadow::dark_shade()
        .black()
        .on_dark_gray()
        .offset(Offset::new(2, 1));

    let block = Block::bordered()
        .title("Confirm")
        .shadow(shadow);

    frame.render_widget(
        Paragraph::new("Delete this item?\n\n[y] Delete  [Esc] Cancel")
            .block(block),
        area,
    );
}
```

`Rect::centered` requires **0.30.0+**; `Shadow` and `Block::shadow` require **0.30.1+**. The shadow paints outside the cleared rectangle, offset two columns right and one row down. Choose its colors from your theme.

At 80 columns this dialog is 48 columns wide; in a 60-column split it is 36:

```text
80 columns                     60 columns
      + Confirm --------+          + Confirm --------+
      | Delete this item?|          | Delete this item?|
      |                  |          |                  |
      |[y] Delete [Esc]… |          |[y] Delete [Esc]… |
      +------------------+          +------------------+
```

Recompute the rectangle each frame so resizing recenters it. For longer messages, wrap and allocate enough height; below your minimum usable size, show a “terminal too small” message. Keep one dialog border, and route input exclusively to the dialog while it is open—`Clear` fixes rendering, but does not create modal focus.