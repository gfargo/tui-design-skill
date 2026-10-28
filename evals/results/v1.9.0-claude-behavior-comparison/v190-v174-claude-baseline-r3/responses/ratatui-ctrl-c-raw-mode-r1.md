Your app's code isn't in this directory, so I can't point at your exact lines. The cause is almost always the same, though.

## Why Ctrl+C does nothing

Ratatui apps put the terminal in **raw mode** (`crossterm::terminal::enable_raw_mode()`, which `ratatui::init()` also does). Raw mode turns off the terminal's `ISIG` flag. Normally that flag makes the terminal turn Ctrl+C into a `SIGINT` signal. With it off, no signal is sent. Ctrl+C arrives as a normal key event:

```rust
KeyEvent { code: KeyCode::Char('c'), modifiers: KeyModifiers::CONTROL, .. }
```

If your handler only matches `KeyCode::Char('q')`, this event goes nowhere. Installing a `ctrlc` or `SIGINT` handler won't help either, because no signal is ever raised.

There's a second, quieter bug: if you match `KeyCode::Char('c')` without checking modifiers, a plain `c` and Ctrl+C trigger the same action.

## Recommended key handling

```rust
use crossterm::event::{self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers};

fn handle_event(app: &mut App) -> std::io::Result<()> {
    if let Event::Key(key) = event::read()? {
        // Windows (and kitty keyboard protocol) also emit Release/Repeat events
        if key.kind != KeyEventKind::Press {
            return Ok(());
        }
        handle_key(app, key);
    }
    Ok(())
}

fn handle_key(app: &mut App, key: KeyEvent) {
    // Global quit: always works, regardless of mode/focus
    if key.modifiers.contains(KeyModifiers::CONTROL)
        && matches!(key.code, KeyCode::Char('c') | KeyCode::Char('C'))
    {
        app.should_quit = true;
        return;
    }

    match app.mode {
        // In text-entry modes, 'q' must type a 'q', not quit
        Mode::Editing => match key.code {
            KeyCode::Esc => app.mode = Mode::Normal,
            KeyCode::Char(c) => app.input.push(c),
            KeyCode::Backspace => { app.input.pop(); }
            _ => {}
        },
        Mode::Normal => match key.code {
            KeyCode::Char('q') | KeyCode::Esc => app.should_quit = true,
            // ... other bindings
            _ => {}
        },
    }
}
```

What matters here:

1. **Check Ctrl+C first, before mode or focus dispatch.** Users expect it to work from anywhere, including text inputs and popups. Ctrl+D is a reasonable second global quit.
2. **Use `contains(CONTROL)`, not `== CONTROL`.** With Caps Lock on, or on some terminals, other modifier bits may be set too.
3. **Filter to `KeyEventKind::Press`.** Otherwise you can act twice on Windows.
4. **Keep `q` mode-dependent.** It should quit in normal mode, but in an input field it has to type a `q`.
5. **Optional:** if quitting could lose unsaved work, have Ctrl+C open a confirm prompt or require a second press, but never make it do nothing.

## Restoring the terminal

Make sure every way of exiting restores the terminal, including errors and panics. If you're on Ratatui 0.28.1 or later, `ratatui::init()` installs a panic hook that does this for you:

```rust
fn main() -> std::io::Result<()> {
    let mut terminal = ratatui::init();
    let result = run(&mut terminal);
    ratatui::restore();
    result
}
```

If you set up raw mode manually, also call `disable_raw_mode()` and `LeaveAlternateScreen` in a panic hook. Otherwise a crash leaves the user's shell broken.

If you share your event-loop code, I can show you the exact change.
