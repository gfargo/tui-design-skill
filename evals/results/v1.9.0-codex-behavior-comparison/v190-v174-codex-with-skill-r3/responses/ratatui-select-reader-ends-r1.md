**Your app keeps ticking but loses keyboard input**, potentially leaving the user unable to quit.

If the reader drops the last sender, `rx.recv()` drains buffered events, then returns `None`. That doesn’t match `Some(event)`, so Tokio disables that branch **for the current `select!` call**. The tick branch still runs. Each loop iteration re-enables the receive branch, which again returns `None` and gets disabled. This does **not** cause a busy loop with the tick branch present.

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

If another sender clone remains alive, the channel won’t close; receiving simply waits while ticks continue. Drop unused sender clones.

Keep the reader’s `JoinHandle` to observe failures, and ensure exiting this loop reaches terminal restoration. Channel closure alone doesn’t tell you whether the reader ended normally, encountered an I/O error, or panicked.