**Handle Ctrl+C explicitly in your event loop.** With the usual Crossterm backend, raw mode disables the terminal driver’s automatic SIGINT behavior. Ctrl+C arrives as `KeyCode::Char('c')` with the `CONTROL` modifier; a handler that only checks `q` ignores it. Ratatui doesn’t supply your application’s key policy.

For a simple, single-view app:

```rust
use ratatui::crossterm::event::{
    Event, KeyCode, KeyEventKind, KeyModifiers,
};

if let Event::Key(key) = event::read()? {
    if key.kind == KeyEventKind::Press {
        match key.code {
            KeyCode::Char('c')
                if key.modifiers.contains(KeyModifiers::CONTROL) =>
            {
                self.should_quit = true;
            }
            KeyCode::Char('q') if key.modifiers.is_empty() => {
                self.should_quit = true;
            }
            _ => {}
        }
    }
}
```

For richer apps, use this policy:

- **Ctrl+C:** cancel running work first; otherwise quit from anywhere. Handle it before passing input to widgets.
- **`q`:** type a letter in text fields, go back in nested views, quit at the root.
- **Esc:** cancel, close the top overlay, clear search/filter, or go back—one applicable step per press. At the root, do nothing.
- **Unsaved work:** warn before quitting; a second Ctrl+C within about two seconds can confirm. Idle quits need no confirmation.

Every quit path should leave the loop through the same cleanup. Prefer `ratatui::run(...)` on current Ratatui; avoid `process::exit()` in the key handler, which bypasses normal cleanup. Show these controls in the footer and test Ctrl+C as well as `q`.