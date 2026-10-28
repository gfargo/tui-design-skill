If the reader task exits **and all `Sender` handles are dropped**, `rx.recv()` drains any buffered events, then returns `None`.

Your `Some(event)` pattern won’t match `None`, so Tokio disables that branch for the remainder of that `select!` call. The tick branch remains active, so the app **keeps ticking indefinitely** unless `app.quit` becomes true. It doesn’t automatically quit or panic.

Each loop iteration tries the receive branch again, but the timer still makes it wait; this alone doesn’t cause a busy loop.

To quit when the channel closes, handle `None` explicitly:

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

If another sender handle remains alive, the receive instead stays pending once the buffer is empty—even though the reader task has exited.