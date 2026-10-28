Render the main view first, then **`Clear` the dialog’s rectangle before rendering the `Paragraph`**. A bordered paragraph doesn’t erase existing characters in its blank cells.

With **Ratatui 0.30.1+**, centering and a drop shadow are built in:

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
        Constraint::Length(7),
    );

    frame.render_widget(Clear, area);

    let shadow = Shadow::dark_shade()
        .black()
        .on_dark_gray()
        .offset(Offset::new(2, 1));

    let dialog = Paragraph::new(
        "Delete this item?\n\n\
         y: delete   n / Esc: cancel",
    )
    .block(Block::bordered().title("Confirm").shadow(shadow));

    frame.render_widget(dialog, area);
}
```

The order matters: **main view → clear dialog area → dialog with shadow**. The shadow paints outside the cleared rectangle; it’s a cell-based effect, without blur or transparency.

`Rect::centered` requires **0.30.0+**; `Shadow` and `Block::shadow` require **0.30.1+**. On older versions, center using horizontal and vertical `Layout` splits, and paint an offset background rectangle before clearing and drawing the dialog.

At 80 columns the dialog is 48 cells wide; at 60 it’s 36. Both fit this prompt. Recompute from `frame.area()` each draw, and use a compact or “terminal too small” state if the prompt and controls cannot fit. Keep one dialog border, route input exclusively to the modal while open, and make Esc cancel.