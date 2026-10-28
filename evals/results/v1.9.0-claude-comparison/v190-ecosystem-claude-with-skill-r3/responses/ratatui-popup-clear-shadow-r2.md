The text shows through because Ratatui draws into a single buffer. `Paragraph` and `Block` only write the cells they use, so any blank cell in your dialog still holds whatever the main view drew there. To fix it, render `Clear` over the dialog's rect before you render the dialog.

## Ratatui 0.30.1+ (centering, clearing and a shadow)

```rust
use ratatui::layout::{Constraint, Offset};
use ratatui::widgets::{Block, Clear, Paragraph, Shadow};
use ratatui::{style::Stylize, Frame};

fn draw_confirm(frame: &mut Frame, message: &str) {
    // 1. Center it (Rect::centered, 0.30.0+)
    let area = frame.area().centered(Constraint::Percentage(60), Constraint::Length(5));

    // 2. Wipe the cells underneath so nothing bleeds through
    frame.render_widget(Clear, area);

    // 3. Drop shadow (Block::shadow, 0.30.1+), drawn on the cells beside the block
    let shadow = Shadow::dark_shade().black().on_dark_gray().offset(Offset::new(2, 1));
    let block = Block::bordered().title("Confirm").shadow(shadow);

    frame.render_widget(Paragraph::new(message).block(block), area);
}
```

Call this **after** you render the main view in the same `draw` closure. Whatever is drawn last ends up on top.

The shadow is drawn on cells outside `area`, which `Clear` doesn't touch. That's what makes it look like it sits on top of the background. Because it uses `▓` shade characters, it also stays visible under `NO_COLOR`.

## On older Ratatui (before 0.30)

You can center the dialog with `Flex::Center`, and draw the shadow yourself by filling an offset rect before you clear the dialog area:

```rust
use ratatui::layout::{Constraint, Flex, Layout, Rect};
use ratatui::style::{Color, Style};

fn centered(area: Rect, w: Constraint, h: Constraint) -> Rect {
    let [area] = Layout::horizontal([w]).flex(Flex::Center).areas(area);
    let [area] = Layout::vertical([h]).flex(Flex::Center).areas(area);
    area
}

// in draw:
let area = centered(frame.area(), Constraint::Percentage(60), Constraint::Length(5));
let shadow = Rect { x: area.x + 2, y: area.y + 1, ..area }.intersection(frame.area());
frame.render_widget(Block::new().style(Style::new().bg(Color::DarkGray)), shadow); // shadow first
frame.render_widget(Clear, area);                                                   // then clear
frame.render_widget(Paragraph::new(message).block(Block::bordered().title("Confirm")), area);
```

The order matters here. Draw the shadow, then `Clear`, then the dialog, so the dialog covers the part of the shadow that sits behind it.

## Dialog design notes

- **Size:** Use 60–80% of the width, cap prose at about 80 columns, and keep it at least 30 columns wide. Something like `Constraint::Percentage(60)` combined with `.min(80)` on the width keeps it readable on wide terminals. Placing it slightly above vertical center tends to look more balanced than exact center.
- **Don't rely on dimming or the shadow to show it's a dialog.** Some terminals ignore the faint attribute and color may be off. The border, the title and changed footer hints (`y confirm ⋅ n/Esc cancel`) should make the dialog obvious on their own.
- **Focus and keys:** While the dialog is open it should capture all input. `Esc` closes it. For destructive actions, make **No** the default (`Delete 3 files? [y/N]`), so pressing Enter by reflex doesn't destroy anything.
- **Small terminals:** At 60 columns, 60% width is 36 columns. Check that your message wraps inside that width. A `Length(5)` height fits 3 lines of text, so add `.wrap(Wrap { trim: true })` and size the height from the wrapped line count if your messages vary in length.
