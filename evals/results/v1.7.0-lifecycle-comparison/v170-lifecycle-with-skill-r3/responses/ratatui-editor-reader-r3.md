Make terminal ownership exclusive. The input task must not coexist with Vim.

1. Cancel the `EventStream` task and await its join; discard any queued app input.
2. Restore the TUI completely: disable raw mode, leave alt-screen, disable mouse capture if enabled, show cursor, flush (`ratatui::try_restore()`).
3. Spawn/wait for Vim with inherited stdio.
4. **Regardless of Vim’s launch/wait/exit result**, attempt `ratatui::try_init()` again.
5. Use the new terminal instance, clear/invalidate it, force a full redraw.
6. Only then create a **fresh** `EventStream` task and resume input.

The important ordering is `stop reader → restore → child → re-init → start reader`. A live `EventStream` can consume Vim’s bytes or retain partially parsed input, which explains both the garbage at launch and the corrupted redraw afterward. Ratatui 0.30’s `try_init`/`try_restore` are the appropriate fallible ownership transitions. [Ratatui initialization docs](https://docs.rs/ratatui/latest/ratatui/init/index.html)

Do not use `?` on Vim’s result before re-entry:

```rust
let vim: Result<ExitStatus, io::Error> = run_vim().await;
let resume: Result<DefaultTerminal, io::Error> = resume_tui();

match (vim, resume) {
    (Ok(status), Ok(terminal)) => { /* redraw, restart input; then handle status */ }
    (Err(vim), Ok(terminal)) => { /* redraw, restart input; report Vim error */ }
    (Ok(status), Err(resume)) => {
        // report: “Vim exited {status}; terminal re-entry failed: {resume}”
    }
    (Err(vim), Err(resume)) => {
        // return one error type containing *both* errors
    }
}
```

An exit status such as `1` is an `Ok(ExitStatus)`, not a spawn/wait error—preserve and report it too. The key is to capture both outcomes before deciding what to return.

For shutdown, install a Unix signal watcher for `SignalKind::terminate()` and convert SIGTERM into the same `Shutdown` event / `CancellationToken` used by normal quit. The main lifecycle owner then stops tasks, handles any active child, restores the terminal, and returns normally. Do not call `process::exit` from the signal task; it skips Rust destructors and bypasses structured cleanup. [Tokio SIGTERM API](https://docs.rs/tokio/latest/tokio/signal/unix/struct.SignalKind.html)

While waiting on Vim, also select on that shutdown token. On SIGTERM, send Vim a graceful SIGTERM (and wait/reap it); only escalate after a timeout if necessary. On Unix, Tokio `Child::kill()` / `start_kill()` use **SIGKILL**, so Vim—and any process receiving SIGKILL—cannot run cleanup. [Tokio child termination semantics](https://docs.rs/tokio/latest/tokio/process/struct.Child.html)
