You need three things: a centered rect, the `Clear` widget, and `Block::shadow`. Render the popup last in the same `draw` closure, after the main view.

```rust
use ratatui::layout::{Constraint, Offset};
use ratatui::widgets::{Block, Clear, Paragraph, Shadow};
use ratatui::{style::Stylize, Frame};

fn draw_confirm(frame: &mut Frame, message: &str) {
    // 1. Center it (Rect::centered, Ratatui 0.30.0+)
    let area = frame.area().centered(Constraint::Percentage(60), Constraint::Length(5));

    // 2. Blank the cells first. This fixes the bleed-through.
    frame.render_widget(Clear, area);

    // 3. Drop shadow (Block::shadow, 0.30.1+), offset 2 right and 1 down
    let shadow = Shadow::dark_shade().black().on_dark_gray().offset(Offset::new(2, 1));
    let block = Block::bordered().title("Confirm").shadow(shadow);

    frame.render_widget(Paragraph::new(message).block(block), area);
}
```

## Why the text shows through

Ratatui draws every widget into one cell buffer. `Paragraph` only writes the cells where it has text, and `Block` only writes its border. Every other cell inside the dialog keeps what the main view put there. `Clear` resets every cell in the rect, so you have to render it into the popup's area just before the popup. You need it any time one widget sits on top of another.

## Shadow notes

- The shadow is drawn on the cells beside and below the block, outside the area you cleared. It covers what's underneath with shade characters, so you don't need a second `Clear` for it.
- Make sure there's room for it. With `Offset::new(2, 1)`, the dialog needs at least 2 free columns on its right and 1 free row below it. With `Percentage(60)` centering that's never an issue except on tiny terminals.
- Shade characters work without color, so the shadow still shows under `NO_COLOR`.

## On older Ratatui (before 0.30)

`Rect::centered` and `Block::shadow` don't exist there. Center with a flex layout instead:

```rust
use ratatui::layout::{Flex, Layout};

let [area] = Layout::horizontal([Constraint::Percentage(60)]).flex(Flex::Center).areas(frame.area());
let [area] = Layout::vertical([Constraint::Length(5)]).flex(Flex::Center).areas(area);
```

For the shadow, render `Block::new().on_dark_gray()` into the dialog's rect shifted by (2, 1). Clip that rect to `frame.area()` first. Then render `Clear` and the dialog on top. Upgrading is simpler.

## Dialog details worth getting right

- **Size:** keep the width between 60–80% of the terminal, no wider than about 80 columns for prose and no narrower than 30. `Percentage(60)` is very wide on a 200-column terminal, so consider capping it, e.g. `Constraint::Length(area.width.clamp(30, 80) * 6 / 10)`. Placing it slightly above vertical center reads better than exact center.
- **Show it's a dialog without relying on color:** you can dim the background with the faint style, but some terminals ignore it. The border, the "Confirm" title, and the key hints should make the dialog obvious on their own. Change the footer to something like `y confirm · n/Esc cancel`.
- **Behavior:** while it's open, the dialog takes all keyboard input. `Esc` closes it, and only one dialog is open at a time. Make No the default (`[y/N]`). For truly destructive actions, consider asking the user to type the name of what they're deleting instead of pressing y.
- **Small terminals:** at 60 columns, 60% is 36 columns, which still fits. Check that your message wraps (`Paragraph::wrap(Wrap { trim: true })`) and that the height you give it fits the wrapped lines. Otherwise the last line, often the question itself, gets cut off.
