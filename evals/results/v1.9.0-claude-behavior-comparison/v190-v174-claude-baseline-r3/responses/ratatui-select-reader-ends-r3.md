## Short answer

The app keeps running and keeps ticking, but it stops getting input. Raw mode turns Ctrl+C into an ordinary key event instead of a SIGINT, so nothing can get to `app.quit`. The user is stuck in a TUI that ignores every key and has to kill it from another terminal. Nothing panics or logs, so it looks like a hang.

## Why

When the reader task exits, its `Sender` is dropped. What happens next depends on whether any other senders exist.

**Case 1: the reader held the only `Sender`.**
- `rx.recv()` returns `None` right away, every time it's polled.
- `None` doesn't match the `Some(event)` pattern. `select!` doesn't treat that as an error. It disables that branch for the current call and keeps waiting on the other branches.
- `tick.tick()` fires, `on_tick()` runs, and the loop starts again.
- On the next iteration, `recv()` returns `None` immediately again, the branch is disabled again, and so on.

So the loop doesn't spin at 100% CPU. It wakes once per tick and never handles input. You also don't get the `select!` panic for "all branches disabled", because the tick branch never gets disabled.

**Case 2: another `Sender` clone is still alive.** For example, the app holds a `tx` clone so background tasks can send events. Then `recv()` never returns `None`. It just stays pending forever. You get the same symptom: ticks keep running and input is dead.

**Common reasons the reader exits:**
- `event::read()` / `EventStream` returns an error (stdin closed, EIO after the terminal goes away) and the task uses `?` or `break`.
- A panic inside the task. Tokio catches it and stores it in the `JoinHandle`, which nobody awaits, so nobody sees it.
- The task stops when `tx.send()` fails. That only happens if the receiver was dropped, so it's less likely here.

## Fixes

**1. Handle `None` explicitly instead of filtering it out with the pattern:**

```rust
loop {
    tokio::select! {
        maybe = rx.recv() => match maybe {
            Some(event) => app.handle(event),
            None => break, // or return Err(anyhow!("input reader stopped"))
        },
        _ = tick.tick() => app.on_tick(),
    }
    if app.quit { break }
}
```

This covers Case 1 only. If other `Sender` clones exist (Case 2), `None` never arrives.

**2. Watch the reader's `JoinHandle` too.** This catches both cases and also surfaces panics:

```rust
let mut reader = tokio::spawn(read_events(tx));

loop {
    tokio::select! {
        res = &mut reader => {
            // Ok(Ok(())) = clean exit, Ok(Err(e)) = io error, Err(e) = panic/cancel
            break; // after logging/propagating res
        }
        Some(event) = rx.recv() => app.handle(event),
        _ = tick.tick() => app.on_tick(),
    }
    if app.quit { break }
}
```

**3. Or drop the separate task.** With crossterm's `event-stream` feature, you can put `EventStream` straight into the `select!`. Then the stream ending or returning an error happens right in your loop where you can't miss it:

```rust
let mut events = crossterm::event::EventStream::new();
loop {
    tokio::select! {
        ev = events.next() => match ev {
            Some(Ok(e)) => app.handle(e.into()),
            Some(Err(e)) => return Err(e.into()),
            None => break,
        },
        _ = tick.tick() => app.on_tick(),
    }
    if app.quit { break }
}
```

If other tasks still need to send app events, keep the channel for those and handle the terminal stream as a separate branch.

**Also:** make sure every exit path restores the terminal, including errors and panics. `ratatui::init()` / `ratatui::restore()` install a panic hook that does this for you. Otherwise the user is left with a terminal stuck in raw mode on the alternate screen.
