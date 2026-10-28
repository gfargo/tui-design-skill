## Why text shows through

Ratatui renders into one shared buffer for the whole frame. A `Paragraph` only writes cells where it has something to draw: border characters, text glyphs, and style. In the blank areas, whatever the main view wrote earlier in the same frame is still there. The fix is to render `Clear` over the dialog's area first. It resets every cell in that rectangle to empty.

## Full example: centered, cleared, with a drop shadow

```rust
use ratatui::{
    layout::{Constraint, Flex, Layout, Rect},
    style::{Color, Style, Stylize},
    text::Line,
    widgets::{Block, BorderType, Clear, Paragraph, Wrap},
    Frame,
};

/// Returns a `width` x `height` rect centered inside `area`.
fn centered_rect(area: Rect, width: u16, height: u16) -> Rect {
    let [area] = Layout::horizontal([Constraint::Length(width)])
        .flex(Flex::Center)
        .areas(area);
    let [area] = Layout::vertical([Constraint::Length(height)])
        .flex(Flex::Center)
        .areas(area);
    area
}

fn render_confirm(frame: &mut Frame, message: &str) {
    let area = centered_rect(frame.area(), 44, 7);

    // 1. Shadow: dim the cells offset down/right from the dialog.
    //    Offset x by 2 and y by 1 because terminal cells are about twice as tall as wide.
    let shadow = Rect {
        x: area.x + 2,
        y: area.y + 1,
        ..area
    }
    .intersection(frame.area()); // clamp so it never goes off-screen
    frame
        .buffer_mut()
        .set_style(shadow, Style::new().fg(Color::DarkGray).bg(Color::Black));

    // 2. Wipe what's underneath the dialog itself.
    frame.render_widget(Clear, area);

    // 3. Draw the dialog. Give it an explicit bg so it reads as a solid panel.
    let dialog = Paragraph::new(vec![
        Line::from(message),
        Line::from(""),
        Line::from(vec!["[Y]".bold().green(), "es   ".into(), "[N]".bold().red(), "o".into()]),
    ])
    .centered()
    .wrap(Wrap { trim: true })
    .block(
        Block::bordered()
            .border_type(BorderType::Rounded)
            .title(" Confirm ")
            .title_alignment(ratatui::layout::Alignment::Center),
    )
    .style(Style::new().bg(Color::Rgb(30, 30, 46)).fg(Color::White));

    frame.render_widget(dialog, area);
}
```

Call it **after** rendering the main view in the same `draw` closure:

```rust
terminal.draw(|frame| {
    render_main(frame);
    if app.confirming {
        render_confirm(frame, "Delete 3 files?");
    }
})?;
```

## Notes

- **Order matters:** shadow, then `Clear`, then the dialog. The dialog covers most of the shadow rect, so only an L-shaped strip shows on the right and bottom edges.
- **Why the shadow restyles cells:** it changes the style of the existing cells instead of blanking them. The main view's text stays faintly visible in dark gray, which looks like a real shadow. For a solid block instead, render `Clear` on `shadow` and then set the bg style.
- **Dialog background:** `Clear` resets cells to the terminal's default background. If your app paints a custom background, set a `bg` on the dialog as above, or it will look like a hole.
- **Centering helper:** `Flex::Center` needs ratatui 0.26 or later. Recent versions also have centering helpers on `Rect` directly. If you're on something older, the classic three-way `Percentage` split from the old popup example does the same job.
- **Small terminals:** if the terminal is smaller than 44×7, `Length` will shrink the dialog. Consider capping with `width.min(area.width)` or showing a compact fallback.
