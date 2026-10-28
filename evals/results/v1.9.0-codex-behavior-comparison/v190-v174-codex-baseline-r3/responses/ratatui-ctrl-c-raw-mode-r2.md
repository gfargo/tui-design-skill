Ratatui apps typically enable **raw mode**, which disables the terminal’s normal Ctrl+C → `SIGINT` behavior. Ctrl+C arrives as a key event instead, so a handler that only checks for `q` ignores it.

Handle Ctrl+C explicitly alongside `q`. With Crossterm:

```rust
use crossterm::event::{
    Event, KeyCode, KeyEventKind, KeyModifiers,
};

if let Event::Key(key) = event::read()? {
    if key.kind == KeyEventKind::Press {
        let quit = match key.code {
            KeyCode::Char('q') => key.modifiers.is_empty(),
            KeyCode::Char('c' | 'C') => {
                key.modifiers.contains(KeyModifiers::CONTROL)
            }
            _ => false,
        };

        if quit {
            break;
        }
    }
}
```

Use the normal exit path so raw mode and the alternate screen are restored. Avoid calling `process::exit()` inside the handler, since it skips destructors and can leave the terminal in a broken state.

If your app has text input, usually reserve Ctrl+C for quitting globally and treat `q` as quit only outside editing mode.