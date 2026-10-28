If the reader task exits and drops the **last sender**, `rx.recv()` drains any queued events, then returns `None`.

Your `Some(event)` pattern rejects `None`, so Tokio disables that branch **for the current `select!` call**. The tick branch remains active, and your app keeps ticking indefinitely unless `app.quit` becomes true. It doesn’t automatically quit or busy-loop, because it still waits on the timer.

Handle channel closure explicitly if it should end the app:

```rust
loop {
    tokio::select! {
        event = rx.recv() => match event {
            Some(event) => app.handle(event),
            None => break,
        },
        _ = tick.tick() => app.on_tick(),
    }

    if app.quit {
        break;
    }
}
```

If another sender clone remains alive, the channel stays open; receiving simply waits for more events while ticks continue.