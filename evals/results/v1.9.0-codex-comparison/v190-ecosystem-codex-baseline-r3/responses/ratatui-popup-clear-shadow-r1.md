A `Paragraph` only paints its own content and styling; it doesn’t erase everything behind it. Render `Clear` over the dialog’s rectangle first.

Use centered layouts for positioning. A drop shadow can be another rectangle painted slightly down and right, before the dialog:

```rust
use ratatui::{
    layout::{Constraint, Flex, Layout},
    style::{Color, Style},
    widgets::{Block, Borders, Clear, Paragraph, Wrap},
    Frame,
};

fn render_confirm(frame: &mut Frame) {
    let screen = frame.area();

    // Center a 50-column × 7-row dialog.
    let [row] = Layout::vertical([Constraint::Length(7)])
        .flex(Flex::Center)
        .areas(screen);

    let [dialog] = Layout::horizontal([Constraint::Length(50)])
        .flex(Flex::Center)
        .areas(row);

    // Paint an opaque shadow, clipped to the screen.
    let shadow = ratatui::layout::Rect {
        x: dialog.x.saturating_add(2),
        y: dialog.y.saturating_add(1),
        ..dialog
    }
    .intersection(screen);

    frame.render_widget(Clear, shadow);
    frame.render_widget(
        Block::default().style(Style::default().bg(Color::Black)),
        shadow,
    );

    // Erase the underlying view, then draw the dialog.
    frame.render_widget(Clear, dialog);
    frame.render_widget(
        Paragraph::new("Delete this item?\n\n[Y] Confirm   [N] Cancel")
            .wrap(Wrap { trim: true })
            .style(Style::default().fg(Color::White).bg(Color::DarkGray))
            .block(
                Block::default()
                    .title(" Confirm ")
                    .borders(Borders::ALL),
            ),
        dialog,
    );
}
```

Render the main view first, then call `render_confirm(frame)` last.

The shadow is an opaque terminal-cell effect; Ratatui doesn’t provide alpha blending or blurred shadows.