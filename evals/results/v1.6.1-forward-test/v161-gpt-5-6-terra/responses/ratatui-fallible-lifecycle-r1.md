No. Treat `try_init()` and `try_restore()` as *fallible operations*, not transactions.

- `try_init()` may enable raw mode before a later step fails (for example, entering the alternate screen or creating the terminal).
- `try_restore()` restores in sequence; if an early teardown operation fails, later ones may not run.
- A returned `Err` therefore does **not** guarantee the terminal is unchanged or fully restored. [Ratatui `try_init` docs](https://docs.rs/ratatui/latest/ratatui/fn.try_init.html) and [Ratatui `try_restore` docs](https://docs.rs/ratatui/latest/ratatui/fn.try_restore.html)

For a normal full-screen app, prefer `ratatui::run(...)`: it manages initialization, normal cleanup, and a panic hook for you.

```rust
fn main() -> std::io::Result<()> {
    ratatui::run(|terminal| App::default().run(terminal))
}
```

If you need explicit error handling around lifecycle operations, use `try_init`, but make cleanup unconditional and best-effort after *any* setup attempt. Do not use `try_restore()?`, because that can skip remaining cleanup.

```rust
fn restore_best_effort() {
    use crossterm::{
        cursor::Show,
        event::{DisableBracketedPaste, DisableMouseCapture},
        execute,
        terminal::{disable_raw_mode, LeaveAlternateScreen},
    };
    use std::io::stdout;

    let _ = disable_raw_mode();
    let _ = execute!(
        stdout(),
        LeaveAlternateScreen,
        DisableMouseCapture,
        DisableBracketedPaste,
        Show,
    );
}

fn main() -> std::io::Result<()> {
    // Install color-eyre / other panic hooks first.
    let mut terminal = match ratatui::try_init() {
        Ok(terminal) => terminal,
        Err(err) => {
            restore_best_effort();
            return Err(err);
        }
    };

    let result = App::default().run(&mut terminal);
    restore_best_effort();
    result
}
```

Also test this in a PTY by injecting failure at setup and each teardown step, plus a panic path. The goal is not perfect atomicity—which terminal control sequences cannot provide—but idempotent, independent cleanup attempts that leave the user’s shell usable.
