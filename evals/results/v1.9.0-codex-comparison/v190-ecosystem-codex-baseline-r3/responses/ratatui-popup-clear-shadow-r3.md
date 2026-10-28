Render `Clear` over the dialog’s area **before** rendering the `Paragraph`. A bordered widget doesn’t erase existing cells in its blank interior.

Use nested layouts to center it:

```rust
use ratatui::{
    layout::{Constraint, Layout, Rect},
    style::{Color, Style},
    widgets::{Block, Borders, Clear, Paragraph},
    Frame,
};

fn centered_rect(area: Rect, width: u16, height: u16) -> Rect {
    let [_, middle, _] = Layout::vertical([
        Constraint::Percentage((100 - height) / 2),
        Constraint::Percentage(height),
        Constraint::Percentage((100 - height) / 2),
    ])
    .areas(area);

    let [_, center, _] = Layout::horizontal([
        Constraint::Percentage((100 - width) / 2),
        Constraint::Percentage(width),
        Constraint::Percentage((100 - width) / 2),
    ])
    .areas(middle);

    center
}

fn render_confirm(frame: &mut Frame) {
    // Render your main view first.

    let area = centered_rect(frame.area(), 60, 25);

    // Optional shadow: a solid rectangle shifted right and down.
    let shadow = Rect::new(
        area.x.saturating_add(2),
        area.y.saturating_add(1),
        area.width,
        area.height,
    )
    .intersection(frame.area());

    frame.render_widget(Clear, shadow);
    frame.render_widget(
        Block::default().style(Style::default().bg(Color::DarkGray)),
        shadow,
    );

    // Erase underlying content, then draw the dialog.
    frame.render_widget(Clear, area);
    frame.render_widget(
        Paragraph::new("Are you sure?\n\n[Y] Confirm    [N] Cancel")
            .style(Style::default().fg(Color::White).bg(Color::Black))
            .block(
                Block::default()
                    .title("Confirm")
                    .borders(Borders::ALL),
            ),
        area,
    );
}
```

The draw order is: **main view → shadow → clear dialog area → dialog**. Ratatui has no alpha transparency, so this shadow is a solid terminal color. Omit the shadow renders if you only want the centered dialog.