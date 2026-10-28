I didn't find any Rust source in the working directory, so this answer covers the general cause and fix rather than your exact code.

## Why Ctrl+C does nothing

Ratatui apps put the terminal into **raw mode** (`enable_raw_mode()`, or `ratatui::init()`, which calls it for you). Raw mode turns off the terminal's `ISIG` flag. Normally, when that flag is on, the terminal turns Ctrl+C into a `SIGINT` signal that kills the process. With it off, Ctrl+C reaches your app as an ordinary key event:

```rust
KeyEvent { code: KeyCode::Char('c'), modifiers: KeyModifiers::CONTROL, .. }
```

If your handler only matches `KeyCode::Char('q')`, that event is ignored. Nothing kills the process, so the app keeps running.

A related trap: if you match `KeyCode::Char('c')` without checking modifiers, plain `c` and Ctrl+C will trigger the same action.

## Recommended key handling

```rust
use crossterm::event::{self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers};

fn handle_key(&mut self, key: KeyEvent) {
    // On Windows (and with the kitty keyboard protocol) you also get Release/Repeat events
    if key.kind != KeyEventKind::Press {
        return;
    }

    match (key.code, key.modifiers) {
        // Ctrl+C always quits, whatever mode or focus the app is in
        (KeyCode::Char('c'), KeyModifiers::CONTROL) => self.quit(),

        // q / Esc quit only when it makes sense (e.g. not while typing in an input field)
        (KeyCode::Char('q'), KeyModifiers::NONE) | (KeyCode::Esc, _) if !self.editing => self.quit(),

        _ => self.dispatch(key),
    }
}
```

Guidelines:

1. **Check Ctrl+C first and never let anything override it.** Users expect it to work as an emergency exit in every mode, including text-input and modal states. If your app has unsaved work, you can show a "press again to quit" prompt, but don't silently swallow the key.
2. **Match on modifiers explicitly.** Then `c`, `C` and Ctrl+C stay distinct, and `q` typed into a text field doesn't quit.
3. **Filter to `KeyEventKind::Press`.** Otherwise one keypress can fire twice on some platforms.
4. **Restore the terminal on every exit path.** Quitting should break out of the main loop, not call `std::process::exit`, so that `ratatui::restore()` (or `disable_raw_mode` + `LeaveAlternateScreen`) runs. Also install a panic hook that restores the terminal. `ratatui::init()` sets one up for you. Without this, a panic leaves the user's shell in raw mode.
5. **Optional: handle a real `SIGINT` too.** Something like `kill -INT <pid>` from another shell bypasses the keyboard. The `ctrlc` crate or `tokio::signal::ctrl_c()` can set a quit flag that the event loop checks. That's for external signals only; the key-event match above is what fixes the bug your users reported.

If you share your event loop file, I can point to the exact lines to change.
