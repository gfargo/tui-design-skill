The bleed-through happens because ratatui widgets only write the cells they draw on. A `Paragraph`/`Block` doesn't touch the blank cells, and setting a background style only changes colors while leaving the old characters in place. To fix it, render the `Clear` widget over the dialog's area first, then draw the dialog on top.

### Centering

Use `Layout` with `Flex::Center` (ratatui 0.26+):

```rust
use ratatui::layout::{Constraint, Flex, Layout, Rect};

fn centered(area: Rect, width: u16, height: u16) -> Rect {
    let [area] = Layout::horizontal([Constraint::Length(width)])
        .flex(Flex::Center)
        .areas(area);
    let [area] = Layout::vertical([Constraint::Length(height)])
        .flex(Flex::Center)
        .areas(area);
    area
}
```

`Constraint::Percentage(50)` works too if you want the dialog to scale with the terminal. On ratatui 0.30+ you can also write `area.centered(Constraint::Length(w), Constraint::Length(h))`.

### Clear + dialog + shadow

```rust
use ratatui::{
    prelude::*,
    widgets::{Block, BorderType, Clear, Paragraph, Wrap},
};

fn render_confirm(frame: &mut Frame, msg: &str) {
    let screen = frame.area();
    let dialog = centered(screen, 40, 7);

    // 1. Shadow: offset one cell right/down, clamped to the screen
    let shadow = Rect {
        x: dialog.x + 2, // 2 columns looks better since terminal cells are tall
        y: dialog.y + 1,
        ..dialog
    }
    .intersection(screen);
    render_shadow(frame.buffer_mut(), shadow);

    // 2. Wipe the dialog area so nothing underneath shows through
    frame.render_widget(Clear, dialog);

    // 3. The dialog itself, with an explicit background
    let block = Block::bordered()
        .border_type(BorderType::Rounded)
        .title(" Confirm ")
        .title_alignment(Alignment::Center)
        .style(Style::new().bg(Color::Rgb(30, 30, 46)).fg(Color::White));

    let text = Text::from(vec![
        Line::from(msg),
        Line::from(""),
        Line::from(vec![
            Span::styled(" [Y]es ", Style::new().bold().green()),
            Span::raw("   "),
            Span::styled(" [N]o ", Style::new().bold().red()),
        ]),
    ]);

    frame.render_widget(
        Paragraph::new(text)
            .block(block)
            .alignment(Alignment::Center)
            .wrap(Wrap { trim: true }),
        dialog,
    );
}
```

### Two shadow styles

**Translucent shadow:** keeps the text underneath but dims it. This usually looks best:

```rust
fn render_shadow(buf: &mut Buffer, area: Rect) {
    for y in area.top()..area.bottom() {
        for x in area.left()..area.right() {
            if let Some(cell) = buf.cell_mut((x, y)) {
                cell.set_fg(Color::DarkGray).set_bg(Color::Black);
            }
        }
    }
}
```

**Solid shadow:** a plain dark block:

```rust
fn render_shadow(buf: &mut Buffer, area: Rect) {
    Clear.render(area, buf);
    Block::new().style(Style::new().bg(Color::Black)).render(area, buf);
}
```

### Things to watch for

- **Order matters:** shadow, then `Clear`, then dialog, all after the main view has been rendered in the same `draw` closure.
- **Set a background on the dialog.** `Clear` resets cells to the terminal's default colors, so the dialog won't stand out from the main view unless you give it its own `bg`.
- **Clamp the shadow.** Without `.intersection(screen)`, a dialog near the edge can produce a shadow rect outside the buffer, and `cell_mut` will return `None` (or older code using `buf[(x, y)]` will panic).
- **Dimming the whole background:** loop over every cell of `screen` with `set_fg(Color::DarkGray)` before drawing the dialog. This gives a modal "backdrop" effect, and you can use it alongside the shadow or instead of it.
