Give the terminal one owner at a time:

1. Tell the event-reader task to quiesce; it must stop reading and acknowledge completion. Drain/drop its queued events before proceeding.
2. Only after that acknowledgement, restore the terminal for the child: disable mouse/paste modes, show cursor, leave the alternate screen, disable raw mode, and flush.
3. Run and wait for Vim in the foreground.
4. **Always** attempt re-entry—even if spawning Vim fails or Vim exits nonzero: enable raw mode, enter the alternate screen, re-enable required modes, clear/reset and redraw.
5. Only after re-entry succeeds, start the event-reader again.

Do not let the Tokio reader race Vim for stdin; Crossterm permits only one event-reading approach at a time, and raw mode changes how input—including Ctrl-C—is handled. [Crossterm events](https://docs.rs/crossterm/latest/crossterm/event/), [raw/alternate-screen behavior](https://docs.rs/crossterm/latest/crossterm/terminal/)

Preserve both errors by recording the child result first, then attempting restoration, and matching both results rather than using `?` between them:

```rust
let vim = run_vim();          // includes nonzero exit status
let resume = tui.resume();    // always attempted

match (vim, resume) {
    (Ok(()), Ok(())) => Ok(()),
    (Err(vim), Ok(())) => Err(Error::Vim(vim)),
    (Ok(()), Err(resume)) => Err(Error::Resume(resume)),
    (Err(vim), Err(resume)) => Err(Error::VimAndResume { vim, resume }),
}
```

Treat a nonzero Vim status as `Vim(...)`, but never skip re-entry because of it.

Route `SIGTERM` into the same cooperative shutdown path as “Quit”: await `tokio::signal::unix::signal(SignalKind::terminate())?.recv()`, cancel/quiesce and join the reader, restore the terminal, then return from `main`. Don’t call `process::exit` in the signal branch. Tokio exposes `SignalKind::terminate()` specifically for SIGTERM. [Tokio signal docs](https://docs.rs/tokio/latest/tokio/signal/unix/struct.SignalKind.html)

`SIGKILL` is the hard termination path that cannot run cleanup at all. Separately, `std::process::exit` also bypasses Rust destructors, so it must not be your normal shutdown mechanism. [Rust `process::exit`](https://doc.rust-lang.org/std/process/fn.exit.html)
