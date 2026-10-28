**Short version:** your app keeps running and redrawing on every tick, but it never receives input again. The user can't quit, and Ctrl-C doesn't help either. It looks like a hang, not a crash.

## What happens, step by step

1. **The reader task exits** (EOF, an error from `event::read()`, or a panic) and drops its `Sender`.
2. **`rx.recv()` returns `None`** right away, and keeps doing so on every later call, once every sender is gone.
3. **`tokio::select!` disables that branch for this iteration.** `None` doesn't match the pattern `Some(event)`, and select! treats a failed pattern match as "disable this branch and keep waiting on the others." It doesn't panic or break.
4. **The tick branch still fires**, so `app.on_tick()` runs and the loop goes around again.
5. **Each new `select!` polls `recv()` again.** It gets `None` again, disables the branch again, and waits for the next tick. This isn't a CPU-burning busy loop, but it is a permanent zombie state.
6. **`app.quit` never becomes true**, assuming only key events set it, so you never `break`.

## Why it's worse than it sounds

- **Ctrl-C does nothing.** In raw mode, Ctrl-C arrives as a key event, not as SIGINT. The only way out is to kill the process from another terminal.
- **Panics are hidden.** If the reader task panicked, Tokio catches it and stores it in the `JoinHandle`, which you're probably not awaiting. The default panic message goes to stderr while you're in the alternate screen and raw mode, so it's invisible or garbled.
- **The terminal stays broken.** When you finally kill the process, your cleanup code doesn't run, so raw mode and the alternate screen are left enabled.
- **A variant: if anything else holds a `tx` clone** (common if the app sends itself events), `recv()` never returns `None`. It just waits forever. The symptoms are the same, and the cause is harder to spot.
- **A trap for later:** if you ever remove the tick branch, every branch can end up disabled, and `select!` panics unless you add an `else` arm.

## Fixes

**1. Handle `None` explicitly:**

```rust
loop {
    tokio::select! {
        maybe_event = rx.recv() => match maybe_event {
            Some(event) => app.handle(event),
            None => break, // reader is gone: shut down (or return an error)
        },
        _ = tick.tick() => app.on_tick(),
    }
    if app.quit { break }
}
```

**2. Notice when the reader dies, and why.** Keep the `JoinHandle` and add it as a branch:

```rust
res = &mut reader_handle => {
    // Err(JoinError) = panic/cancel; Ok(Err(e)) = io error from crossterm
    return Err(anyhow!("input reader exited: {res:?}"));
}
```

Have the reader return `io::Result<()>` instead of silently ending its loop on error.

**3. Or remove the separate task.** Enable crossterm's `event-stream` feature and select on `EventStream` directly:

```rust
let mut events = crossterm::event::EventStream::new();
// ...
maybe = events.next() => match maybe {
    Some(Ok(ev)) => app.handle(ev.into()),
    Some(Err(e)) => return Err(e.into()),
    None => break,
},
```

**4. Restore the terminal no matter how you exit.** Use a panic hook (`ratatui::init()` installs one for you, or call `ratatui::restore()` in a custom hook) together with a drop guard. That way an error or panic leaves the terminal usable and the message readable.

I'd do #1 or #3, plus #4. The main point is to treat "input source ended" as an explicit shutdown or error, not something select! silently skips.
