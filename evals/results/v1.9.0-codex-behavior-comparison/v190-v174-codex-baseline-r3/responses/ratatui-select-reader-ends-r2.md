If the reader task exits **and drops the last sender**, `rx.recv()` drains any queued events, then returns `None`.

Your `Some(event)` pattern doesn’t match `None`, so Tokio disables that branch **for the current `select!` call**. The tick branch still runs, and the outer loop continues—effectively ticking forever unless `app.on_tick()` sets `app.quit`.

Handle channel closure explicitly:

```rust
loop {
    tokio::select! {
        event = rx.recv() => match event {
            Some(event) => app.handle(event),
            None => break, // All senders dropped; queued events drained.
        },
        _ = tick.tick() => app.on_tick(),
    }

    if app.quit {
        break;
    }
}
```

If another sender clone remains alive, the channel stays open and `recv()` waits instead. A reader task panic also won’t automatically propagate to this loop; observe its `JoinHandle` if you need to distinguish a panic from normal shutdown.