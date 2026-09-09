Give terminal ownership to exactly one lifecycle controller:

`pause input → join reader → restore terminal → run Vim → re-enter terminal → clear/redraw → start fresh reader`

More precisely:

1. Stop drawing and cancel the `EventStream` task.
2. Await its `JoinHandle` (abort it only as a fallback, then await it). Discard queued pre-launch events; otherwise Vim’s bytes can later be handled as TUI input.
3. Call `ratatui::try_restore()` and, if you hid it yourself, show the cursor. Do not start Vim unless this succeeds.
4. Spawn Vim with inherited `stdin`, `stdout`, and `stderr`; wait for it.
5. **Regardless of Vim’s exit status or wait error**, call `ratatui::try_init()` to reclaim raw mode and the alternate screen.
6. On successful re-entry, `terminal.clear()?`, force a full draw, and create a new event-reader task. Never reuse the old reader.

Ratatui’s `try_restore` deliberately lets you retain cleanup errors; it disables raw mode then leaves the alternate screen. [`try_restore` documentation](https://docs.rs/ratatui/0.30.2/ratatui/fn.try_restore.html)

Do not use `?` on Vim’s result before re-entry. Preserve the pair explicitly:

```rust
let vim = run_vim().await;              // Result<ExitStatus, io::Error>
let resume = ratatui::try_init();       // Result<DefaultTerminal, io::Error>

match (vim, resume) {
    (Ok(status), Ok(terminal)) => Ok((status, terminal)),
    (Err(vim), Ok(terminal)) => Err(LaunchError::Vim { vim, terminal }),
    (Ok(status), Err(resume)) => Err(LaunchError::Resume { status, resume }),
    (Err(vim), Err(resume)) => Err(LaunchError::VimAndResume { vim, resume }),
}
```

Treat a nonzero `ExitStatus` as an editor outcome, not a reason to skip restoration. A composite error type is the important part: neither failure should overwrite the other.

For `SIGTERM`, create a Unix Tokio signal stream with `SignalKind::terminate()` and send its notification to that same lifecycle controller/event bus—not directly to a background task that manipulates terminal state. On receipt: stop/join input, terminate and reap any active child (or its dedicated process group if it may have descendants), restore the terminal, then return normally with an appropriate termination result/status. `tokio::signal::ctrl_c()` is not a SIGTERM handler. [`SignalKind::terminate`](https://docs.rs/tokio/latest/tokio/signal/unix/struct.SignalKind.html#method.terminate)

`SIGKILL` (`kill -9`) is the hard-termination path that cannot run cleanup: no signal handler, `Drop`, panic hook, terminal restore, or child reaping can be guaranteed.
