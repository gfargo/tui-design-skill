Make terminal ownership exclusive—never let Vim and the Crossterm reader own stdin at once:

1. Cancel the `EventStream` task and **await its join**.
2. Restore Ratatui/Crossterm shell state (raw mode off, leave alt screen, cursor visible).
3. Spawn Vim inheriting the terminal and wait for it.
4. Reinitialize the TUI terminal, clear it, restart the event-reader task, reload data Vim could have changed, and force a full draw.

The important detail is the join in step 1: merely signalling cancellation is not enough. A still-running reader can consume bytes or terminal capability replies while the terminal is being re-entered.

Treat Vim’s outcome and re-entry as independent results; do not use `?` between them:

```rust
let vim = run_vim().await; // includes nonzero status as a failure outcome

let reentry = reenter_terminal()
    .and_then(|mut terminal| {
        terminal.clear()?;
        Ok(terminal)
    });

match (vim, reentry) {
    (Ok(status), Ok(terminal)) if status.success() => {
        // restart input task, reload state, full redraw
    }
    (vim_result, reentry_result) => {
        // return/report an aggregate containing *both* failures,
        // e.g. “Vim exited 1; terminal re-entry failed: …”
    }
}
```

In practice, normalize a nonzero `ExitStatus` into your app’s error type, then combine errors with an aggregate/compound error type. Preserve the child result before attempting `try_init`, `clear`, or `draw`, because any of those can otherwise replace the original Vim failure.

For SIGTERM, install a Tokio Unix signal listener and send a `Quit`/cancellation event into the application loop. The loop should stop and join background tasks, then return through `ratatui::run(...)` (or call `ratatui::restore()` on the retained loop result). Do not rely on default SIGTERM delivery: it terminates the process without Rust unwinding or terminal cleanup.

`SIGKILL` is the hard-termination path that cannot run cleanup—no signal handler, `Drop`, panic hook, or terminal restoration can execute.
