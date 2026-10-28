## Why Ctrl+C does nothing

Your app runs in **raw mode**. `ratatui::init()` and `ratatui::run()` turn it on, and every full-screen TUI uses it. In raw mode the terminal driver stops turning Ctrl+C into SIGINT. The keystroke reaches your app as a normal key event: `KeyCode::Char('c')` with `KeyModifiers::CONTROL`. No signal is sent, so the OS never kills the process. If your match only handles `'q'`, the event lands in `_ => {}` and is dropped.

Ratatui won't handle this for you. It sets up the terminal and rendering, but your code owns the event loop and decides what each key does. Ctrl+Z works the same way: in raw mode it's just another key, and suspend only works if you build it.

## What the key handling should be

Users expect each quit key to do something different:

| Key | Behavior |
|---|---|
| **Ctrl+C** | Cancels a running operation if there is one. Otherwise it quits from anywhere, without stepping back through views. If quitting would lose something, the first press shows `Press Ctrl+C again to quit` and a second press within about 2 seconds quits. |
| **q** | Goes back one level in a nested view and quits at the root. In a single-view app it just quits. While a text field has focus, it's a normal letter. |
| **Esc** | Takes the innermost step that applies: cancel, close the overlay, clear the filter, go back. It **never** quits. |

Only ask for confirmation when quitting would lose something, like unsaved edits or jobs that can't resume. An idle quit should never ask.

### Minimal fix (single-view app)

```rust
use ratatui::crossterm::event::{self, Event, KeyCode, KeyEventKind, KeyModifiers};

fn handle_events(&mut self) -> Result<()> {
    if let Event::Key(key) = event::read()? {
        // Windows reports Press and Release; without this every key fires twice
        if key.kind != KeyEventKind::Press {
            return Ok(());
        }
        match key.code {
            // raw mode delivers Ctrl+C as a key event, not SIGINT
            KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                self.should_quit = true
            }
            KeyCode::Char('q') => self.should_quit = true,
            _ => {}
        }
    }
    Ok(())
}
```

Put the Ctrl+C arm **before** any plain `KeyCode::Char(c)` arm. Otherwise a catch-all character handler, such as one feeding a text input, will take it first.

### Fuller version (cancellable work, nested views, unsaved state)

```rust
KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
    if let Some(task) = self.running.take() {
        task.cancel();                         // 1. cancel first, keep old data
    } else if self.has_unsaved() && !self.ctrl_c_armed() {
        self.ctrl_c_at = Some(Instant::now()); // 2. warn once
        self.status = "Press Ctrl+C again to quit".into();
    } else {
        self.should_quit = true;               // 3. quit from anywhere
    }
}
KeyCode::Char('q') if !self.text_input_focused() => {
    if self.view_stack.len() > 1 { self.view_stack.pop(); } else { self.request_quit(); }
}
KeyCode::Esc => self.esc_step(), // cancel → close → clear → back → nothing
```

Here `ctrl_c_armed()` checks whether `ctrl_c_at` is less than about 2 seconds old.

## Make sure quitting restores the terminal

Every quit path should set `should_quit` and let the loop return. Don't call `std::process::exit` from the key handler, because that skips the cleanup.

- With `ratatui::run(...)`, or with `init()`/`restore()` where you call `restore()` even when the loop returns an error, the terminal is reset to normal mode and the alternate screen is closed.
- `restore()` only undoes raw mode and the alternate screen. If you turned on mouse capture, bracketed paste, or keyboard-enhancement flags, turn them off yourself before it runs.

A cheap test: feed a synthetic `KeyEvent::new(KeyCode::Char('c'), KeyModifiers::CONTROL)` into `handle_events` or your update function and check that `should_quit` becomes true. Then run one manual or PTY smoke test to confirm the shell is usable again after Ctrl+C.
