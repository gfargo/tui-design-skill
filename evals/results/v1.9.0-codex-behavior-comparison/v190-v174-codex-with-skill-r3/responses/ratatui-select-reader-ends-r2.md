**The app keeps ticking but loses keyboard input**, potentially leaving users unable to quit.

If the reader drops the **last sender**, `rx.recv()` drains queued events, then returns `None`. Your `Some(event)` pattern rejects `None`, disabling that branch for the current `select!` invocation. The timer still runs, so the loop continues; the branch is retried on each iteration. This does **not** inherently cause a busy loop or panic.

Handle closure explicitly:

```rust
loop {
    tokio::select! {
        event = rx.recv() => match event {
            Some(event) => app.handle(event),
            None => break, // input reader ended
        },
        _ = tick.tick() => app.on_tick(),
    }

    if app.quit {
        break;
    }
}
```

If another sender clone remains alive, the channel stays open and `recv()` waits instead—still leaving the app ticking without keyboard input.

Keep the reader’s `JoinHandle` to detect panics and report reader errors. Route loop exit through terminal cleanup; cancel and await the reader when shutting down normally.