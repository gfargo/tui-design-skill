Your project directory has no source files I could check, so this explanation covers the usual cause rather than your exact code.

## Why Ctrl+C does nothing

A Ratatui app puts the terminal in **raw mode**, either with `ratatui::init()` or `crossterm::terminal::enable_raw_mode()`. Raw mode turns off `ISIG`, so the terminal no longer converts Ctrl+C into a `SIGINT` signal. Instead, Ctrl+C reaches your app as an ordinary key event:

```rust
KeyEvent { code: KeyCode::Char('c'), modifiers: KeyModifiers::CONTROL, kind: KeyEventKind::Press, .. }
```

If your handler only matches `KeyCode::Char('q')`, this event falls through and gets ignored. You switched off the OS-level shortcut, so you have to handle it yourself. Ctrl+Z (suspend) and Ctrl+\ (quit) also stop working in raw mode for the same reason.

## Recommended key handling

```rust
use crossterm::event::{self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers};

fn handle_key(app: &mut App, key: KeyEvent) {
    // Only react to presses. Otherwise Windows (and terminals using the kitty
    // keyboard protocol) also send Release events, so each key fires twice.
    if key.kind != KeyEventKind::Press {
        return;
    }

    match (key.code, key.modifiers) {
        // Ctrl+C always quits, whatever mode or input the app is in.
        (KeyCode::Char('c'), m) if m.contains(KeyModifiers::CONTROL) => app.quit(),

        // `q` / Esc quit only when they aren't being typed into a text field.
        (KeyCode::Char('q'), KeyModifiers::NONE) | (KeyCode::Esc, _)
            if !app.is_editing() => app.quit(),

        _ => app.handle_other(key),
    }
}
```

Some rules to follow:

1. **Check Ctrl+C first and always.** Users expect it to work everywhere. Don't let a modal, text input or other mode capture it.
2. **Use `modifiers.contains(CONTROL)`, not `==`.** Some terminals add other modifier bits, and an exact comparison would miss the key.
3. **Only allow `q` to quit outside text input.** Otherwise users can't type the letter "q" in a field.
4. **Filter on `KeyEventKind::Press`.**
5. **Restore the terminal on every exit path.** Use `ratatui::restore()` or `disable_raw_mode` plus `LeaveAlternateScreen`. If you use `ratatui::init()`, it installs a panic hook that restores the terminal on a panic. If you set up the terminal manually, you need to add that hook yourself, or a panic will leave the user's shell broken.

## Optional

- **A real `SIGINT`** can still arrive from outside, for example `kill -INT <pid>`. If you need to handle it, use the `ctrlc` crate or a `tokio::signal::ctrl_c()` handler that sets an `AtomicBool` your loop checks. This doesn't replace the key-event handler above, because raw mode stops the terminal from sending the signal at all.
- **Ctrl+Z suspend:** if you want it, on Unix you call `restore()`, raise `SIGTSTP`, and run `init()` again once the app resumes.
- Show **"q / Ctrl+C quit"** in a footer or help line so users can find it.

If you paste your event loop, I can show you exactly where the change goes.
