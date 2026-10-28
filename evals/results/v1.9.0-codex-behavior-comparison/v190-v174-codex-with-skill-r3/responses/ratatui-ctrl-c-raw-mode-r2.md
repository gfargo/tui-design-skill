**Bind Ctrl+C explicitly.** Ratatui’s usual Crossterm setup enables raw mode, so the terminal stops turning Ctrl+C into `SIGINT`. It arrives as `KeyCode::Char('c')` with `KeyModifiers::CONTROL`; a handler that only checks `q` ignores it. A SIGINT handler alone won’t fix this.

Use this key policy:

| Key | Behavior |
|---|---|
| `Esc` | Cancel work, close the top overlay, clear search/selection, or go back—one applicable step per press. Never quit at the root. |
| `q` | Go back in nested views; quit at the root. Insert a letter when a text field owns input. |
| `Ctrl+C` | Cancel running work first; otherwise quit from anywhere. If quitting loses work, warn and require confirmation or a second press within about two seconds. |

Route Ctrl+C before focused widgets so they cannot swallow it:

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
                app.cancel_or_request_quit();
            }
            KeyCode::Esc => app.dismiss_innermost(),
            KeyCode::Char('q')
                if key.modifiers.is_empty() && !app.text_input_focused() =>
            {
                app.back_or_request_quit();
            }
            _ => app.handle_focused_key(key),
        }
    }
}
```

The `app` methods above represent your state transitions. For a simple, idle, single-view app, both `q` and Ctrl+C can just set `should_quit = true`.

**Exit through the event loop’s normal cleanup path**, rather than calling `process::exit`. Prefer `ratatui::run(...)` where available; undo any extra terminal modes you enabled. Verify Ctrl+C cancels work, quits while text input has focus, and restores the terminal on exit.