**Why:** Ratatui puts the terminal in raw mode, and raw mode turns off the terminal's signal handling (`ISIG`). So Ctrl+C no longer sends SIGINT to your process. It shows up as an ordinary key event: `KeyCode::Char('c')` with `KeyModifiers::CONTROL`. Your loop only matches `'q'`, so that event falls into the `_ => {}` arm and nothing happens. Ctrl+Z has the same problem: in raw mode it's just a key, so suspend won't work either unless you handle it yourself.

Don't fix this with a SIGINT handler (`ctrlc`, `signal-hook`). Under raw mode no SIGINT is ever sent, so the handler would never fire. Handle Ctrl+C as a key in your event loop.

## What the key handling should be

Use this quit order:

- **Ctrl+C:** if something is running, cancel it. Otherwise quit, from any view, without stepping back through the layers. If quitting would lose something (unsaved edits, jobs that can't resume), the first press shows `Press Ctrl+C again to quit` on the status line, and a second press within about 2 s quits.
- **`q`:** go back one level in a nested view and quit at the root. In a single-view app it just quits. When a text field has focus, `q` types a `q`. Ctrl+C still works there, which is a big reason to support it.
- **`Esc`:** take the innermost step that applies: cancel a running operation, close the top popup, clear a filter, or go back. **At the root it does nothing; `Esc` never quits.**
- Only ask for confirmation when quitting would lose something. Quitting while idle should never ask.
- Every quit path must run the same teardown.

```rust
use std::time::{Duration, Instant};
use ratatui::crossterm::event::{self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers};

fn handle_key(&mut self, key: KeyEvent) {
    // Windows sends Press and Release; act on Press only.
    if key.kind != KeyEventKind::Press {
        return;
    }

    // raw mode delivers Ctrl+C as a key event, not SIGINT
    if key.modifiers.contains(KeyModifiers::CONTROL) {
        match key.code {
            KeyCode::Char('c') => return self.on_ctrl_c(),
            KeyCode::Char('z') => { self.suspend_requested = true; return; }
            _ => {}
        }
    }

    match key.code {
        KeyCode::Char(c) if self.input_focused => self.input.push(c), // 'q' is a letter here
        KeyCode::Esc => self.step_back(),       // cancel → close → clear → back; no-op at root
        KeyCode::Char('q') => {
            if self.at_root() { self.request_quit() } else { self.go_back() }
        }
        _ => {}
    }
}

fn on_ctrl_c(&mut self) {
    if self.task.is_some() {
        self.cancel_task();                      // keep the old data
    } else if !self.would_lose_work() {
        self.should_quit = true;
    } else if self.ctrl_c_armed.is_some_and(|t| t.elapsed() < Duration::from_secs(2)) {
        self.should_quit = true;
    } else {
        self.ctrl_c_armed = Some(Instant::now());
        self.status = "Unsaved changes — press Ctrl+C again to quit".into();
    }
}
```

`request_quit()` follows the same rule: if nothing would be lost, set `should_quit`. Otherwise open `Quit? 2 jobs are still running [y/N]` with No as the default.

## Make sure quitting cleans up

When `should_quit` is set, return normally from the loop and let `ratatui::run(...)` restore the terminal. If you call `init()`/`restore()` yourself, keep the loop's result, call `restore()`, then return the result, so an error can't skip cleanup. Don't call `std::process::exit` from the key handler. It skips the restore and leaves the user's shell in raw mode with no cursor. If you turned on mouse capture, bracketed paste or keyboard-enhancement flags, turn them off before `restore()`, because it only resets raw mode and the alternate screen.

## Related checks

- **Ctrl+Z:** handle it as a key too. Restore the terminal, raise SIGTSTP, then re-init and redraw fully after SIGCONT. Windows has no job control, so offer a drop-to-shell option there instead.
- **SIGTERM:** this is a real signal, but Ratatui won't turn it into an event. Route it into the loop as a quit message (with `signal-hook` or `tokio::signal`) so it goes through the same cleanup.
- **Profiling:** Ctrl+C won't stop `cargo flamegraph` while the app is in raw mode. Quit with the app's own key, or attach with `--pid`.
- **Discoverability:** put `q quit` (or `q back` in nested views) in the footer hints, and build the footer from the same key map so it can't drift.
- **Test it:** feed fake Ctrl+C, `q` and Esc `KeyEvent`s into `handle_key` and check the state: idle Ctrl+C sets `should_quit`; Ctrl+C during a task cancels it and doesn't quit; with unsaved work, the first press arms and the second quits; `q` in a text field adds a character; Esc at the root does nothing. Then run one real-terminal smoke test to confirm Ctrl+C leaves the shell usable.
