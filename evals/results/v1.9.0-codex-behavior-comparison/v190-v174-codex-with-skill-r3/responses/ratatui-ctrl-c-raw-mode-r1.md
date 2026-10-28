**Handle Ctrl+C explicitly in your event loop.** Ratatui’s usual Crossterm setup enables raw mode, so the terminal stops converting Ctrl+C into `SIGINT`. Instead, Crossterm delivers a key event: `Char('c')` with the `CONTROL` modifier. If you only match `q`, Ctrl+C is ignored.

For a simple, single-view app:

```rust
use ratatui::crossterm::event::{
    Event, KeyCode, KeyEventKind, KeyModifiers,
};

if let Event::Key(key) = event {
    if key.kind == KeyEventKind::Press {
        match key.code {
            KeyCode::Char('c')
                if key.modifiers.contains(KeyModifiers::CONTROL) =>
            {
                app.should_quit = true;
            }
            KeyCode::Char('q')
                if key.modifiers.is_empty() =>
            {
                app.should_quit = true;
            }
            _ => {}
        }
    }
}
```

For an app with text input, nested views, or background work, use this policy:

| Key | Behavior |
|---|---|
| **Ctrl+C** | Cancel running work first; otherwise quit from anywhere. Handle before focused widgets consume input. |
| **q** | Type `q` in text fields; otherwise go back one level, quitting only at the root. |
| **Esc** | Take one applicable step: cancel work → close top overlay → clear search/filter/selection → go back. At the root, do nothing. |

If quitting would lose work, warn on the first Ctrl+C (`Press Ctrl+C again to quit`); a second press within about two seconds confirms. Idle exits need no confirmation.

Every quit path should leave the event loop through the **same cleanup path**. Prefer `ratatui::run(...)` where available, and undo any extra terminal modes you enabled. Avoid `std::process::exit()` inside the key handler—it bypasses normal cleanup.