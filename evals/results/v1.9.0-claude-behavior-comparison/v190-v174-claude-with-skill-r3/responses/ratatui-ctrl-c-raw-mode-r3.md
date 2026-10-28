## Why Ctrl+C does nothing

Your app runs in raw mode, and that turns off the terminal's own Ctrl+C handling. `ratatui::init()` / `ratatui::run()` switch raw mode on. In normal (cooked) mode, the terminal turns Ctrl+C into SIGINT and the process dies. In raw mode, nothing sends a signal. Ctrl+C reaches your app as a normal key event: `KeyCode::Char('c')` with `KeyModifiers::CONTROL`. If your `match` only checks for `'q'`, that event goes to the `_ => {}` arm and gets dropped.

Two related problems are worth checking:

- **Adding a SIGINT handler (`ctrlc`, `tokio::signal::ctrl_c`) won't fix it.** No SIGINT is sent while raw mode is on. Handle the key event.
- **If the event loop is stuck doing work, no key gets through.** If you do disk, network, or subprocess work on the loop thread, Ctrl+C has to wait behind it even after you bind it. Run that work on a thread or task and send results back through a channel, so the loop can always read keys.

## What the key handling should be

Give each quit key its own role, and send every quit through the same cleanup:

| Key | Behavior |
|---|---|
| `Ctrl+C` | If an operation is running, cancel it. Otherwise quit, from any view. If quitting would lose something (unsaved edits, jobs that can't resume), the first press shows `Press Ctrl+C again to quit` and a second press within about 2 seconds quits. |
| `q` | Quits from the root view. In a nested view it goes back one level. When a text field has focus it's just the letter q. |
| `Esc` | Takes one step back: cancel the running operation, close the top popup, clear a filter, or go back a level. Pressing it at the root does nothing. It never quits. |
| `Ctrl+Z` | Raw mode also stops this from suspending, and Ratatui has no built-in suspend. Either bind it (restore the terminal, send SIGTSTP, set the terminal up again and redraw on `fg`) or don't advertise it. |

```rust
use std::time::{Duration, Instant};
use ratatui::crossterm::event::{self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers};

fn handle_key(&mut self, key: KeyEvent) {
    if key.kind != KeyEventKind::Press {
        return; // Windows also reports Release events
    }

    // Ctrl+C is global: checked before focus routing so text inputs can't swallow it
    if key.code == KeyCode::Char('c') && key.modifiers.contains(KeyModifiers::CONTROL) {
        if let Some(job) = self.running_job.take() {
            job.cancel();                       // first: cancel in-flight work
            self.status = "Cancelled".into();
        } else if self.has_unsaved_work()
            && !self.ctrl_c_armed_at.is_some_and(|t| t.elapsed() < Duration::from_secs(2))
        {
            self.ctrl_c_armed_at = Some(Instant::now());
            self.status = "Unsaved changes — press Ctrl+C again to quit".into();
        } else {
            self.should_quit = true;            // same exit path as `q`
        }
        return;
    }

    if self.text_input_focused() {
        self.input.handle(key);                 // `q` and Esc are just keys here
        return;
    }

    match key.code {
        KeyCode::Char('q') if self.view_stack.len() > 1 => { self.view_stack.pop(); }
        KeyCode::Char('q') => self.request_quit(), // asks [y/N] only if something would be lost
        KeyCode::Esc => self.step_back(),          // cancel → close → clear → back; no-op at root
        _ => { /* app keys */ }
    }
}
```

Set `should_quit` and let the loop return. Don't call `std::process::exit`. When the loop returns, `ratatui::run()` restores the terminal (raw mode and the alternate screen) on every exit path: `q`, the second Ctrl+C, and errors. If you turned on mouse capture, bracketed paste, or keyboard-enhancement flags, `restore()` leaves those on. Turn them off yourself before you return.

## Test it

The handler doesn't need a terminal, so unit-test it with synthetic `KeyEvent`s and check the resulting state:
- When idle, Ctrl+C sets `should_quit`.
- When a job is running, Ctrl+C cancels it and the app keeps running.
- With unsaved work, Ctrl+C asks first.
- `q` typed into a filter field is inserted as text.
- `Esc` at the root does nothing.

Also add one PTY smoke test that presses Ctrl+C and checks that the shell comes back working normally, with no leftover raw mode or hidden cursor.
