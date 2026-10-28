**The app keeps ticking but loses keyboard input**, assuming the reader owned the last sender.

After queued events drain, `rx.recv()` returns `None`. Your `Some(event)` pattern doesn’t match, so Tokio disables that branch **for the current `select!` call**. The tick branch remains active. Each loop iteration repeats this behavior; closure alone causes neither a panic nor a busy loop.

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

Two details matter:

- If another sender clone remains alive, the channel stays open and `recv()` waits instead. Drop unused senders or monitor the reader’s `JoinHandle` directly.
- Channel closure doesn’t explain whether the reader ended normally, encountered an error, or panicked. Preserve its result and await its handle to diagnose that.

Route this exit through terminal cleanup. In raw mode, Ctrl+C normally arrives as a key event, so a dead input reader can also leave the user unable to quit that way.