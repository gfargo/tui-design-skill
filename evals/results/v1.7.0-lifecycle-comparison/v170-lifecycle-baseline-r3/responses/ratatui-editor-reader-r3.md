Treat the terminal as having exactly one input owner at a time:

1. Cancel the `EventStream` task **and await its `JoinHandle`** so its reader is dropped; drain/discard its queued events.
2. Leave TUI mode: disable paste/mouse, show cursor, leave alternate screen, disable raw mode.
3. Spawn/wait for Vim with inherited terminal stdio.
4. Regardless of Vim’s result, re-enter TUI mode (raw mode + alternate screen + options), clear/reset Ratatui’s buffer, and force a full redraw.
5. Only then create/start a fresh Crossterm event-reader task.

Do not merely signal cancellation and immediately start Vim: until the task has exited, it can steal Vim’s keystrokes and consume terminal-query replies (the “garbage” is commonly Vim’s terminal background-color query response). Ratatui explicitly calls out pausing advanced event handlers around external editors. [Ratatui: Spawn External Editor](https://ratatui.rs/recipes/apps/spawn-vim/)

Most importantly, don’t write this:

```rust
let status = Command::new("vim").status()?; // skips re-entry on error
reenter_tui()?;
```

Capture both results, always attempt re-entry, then return a structured/aggregate result:

```rust
let vim: io::Result<ExitStatus> =
    std::process::Command::new("vim").arg(path).status();

let reentry: io::Result<()> = reenter_tui_and_clear(&mut terminal);

match (vim, reentry) {
    (Ok(status), Ok(())) if status.success() => Ok(()),
    (Ok(status), Ok(())) => Err(EditError::VimExited(status)),
    (Err(vim), Ok(())) => Err(EditError::VimIo(vim)),
    (vim, Err(reentry)) => Err(EditError::Reentry { vim, reentry }),
}
```

`EditError::Reentry` should retain the complete `vim: Result<ExitStatus, io::Error>`—a nonzero exit is an `Ok(status)`, not an I/O error—plus the re-entry error. Do not hide either result behind `?`.

Handle `SIGTERM` at the outer Tokio state machine, e.g. with `tokio::signal::unix::signal(SignalKind::terminate())` in the same `select!` that drives application exit. Convert it to a normal `Shutdown::Sigterm` decision, then execute the same ordered shutdown: stop/await reader, restore terminal, and return. If a child is active, make an explicit policy to terminate/await (and, when appropriate, signal) its process group before restoring the terminal; don’t leave it unreaped. Don’t perform terminal I/O inside a signal handler.

`SIGKILL` is the hard-termination path that cannot run cleanup—no signal handler, `Drop`, panic hook, or terminal restore executes. Likewise, avoid relying on `std::process::exit` for cleanup because it bypasses Rust destructors. Ratatui’s normal helpers restore on regular exit/panic, but lifecycle ownership is still yours around an external child. [Ratatui terminal lifecycle](https://docs.rs/ratatui/latest/ratatui/struct.Terminal.html)
