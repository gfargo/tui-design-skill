Ratatui apps typically enable **raw mode**, which disables the terminal’s normal Ctrl+C → `SIGINT` behavior. Ctrl+C becomes a key event, so your event loop must handle it explicitly. A signal handler alone won’t catch it while raw mode is enabled.

With Crossterm, handle both `q` and Ctrl+C:

```rust
use crossterm::event::{
    self, Event, KeyCode, KeyEventKind, KeyModifiers,
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

Checking `Press` avoids handling release events on terminals that report them. Checking Ctrl with `contains` allows additional modifiers, such as Shift.

Exit through your normal cleanup path so raw mode is disabled and the alternate screen is restored; avoid calling `std::process::exit()` directly from the key handler.