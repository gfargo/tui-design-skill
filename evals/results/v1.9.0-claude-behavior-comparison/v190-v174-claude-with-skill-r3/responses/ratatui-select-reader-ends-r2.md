**Short answer:** the app keeps running and ticking, but it can never receive input again. It becomes an unresponsive UI stuck in raw mode, and the user can't quit it from the keyboard.

### Why

1. **The channel closes.** When the reader task exits (EOF, an `Err` from `EventStream`, or a panic), it drops its `tx`. If that was the last sender, `rx.recv()` starts returning `None` right away, every time it's polled.
2. **Your pattern hides the `None`.** In `tokio::select!`, a branch written as `Some(event) = rx.recv()` that gets a value it can't match is **disabled for that one `select!` call**. It isn't an error. `select!` then waits on the remaining branch, `tick.tick()`.
3. **The loop keeps going.** Each pass through the `loop` builds a fresh `select!`. The recv branch returns `None` again, gets disabled again, and the loop waits for the next tick. It doesn't spin the CPU, because the tick still waits, but `app.handle` is never called again.
4. **Nothing can quit it.** `app.quit` is only set from input, so the loop never ends. In raw mode, Ctrl-C arrives as a key event, not as SIGINT, so it goes into the dead channel too. The user has to kill the process from another terminal, and the terminal is left in raw mode or the alternate screen.

Two related cases:
- **The app still holds a `tx` clone** (for example, to pass to worker tasks). The channel never closes, so `recv()` just waits forever. You get the same frozen-input result without even a `None` you could detect.
- **The reader panicked.** The panic is stored in the `JoinHandle`. If you never await the handle, you never see the error.

If the tick branch also stopped being able to complete, every branch would be disabled. `select!` panics in that case unless you give it an `else` branch.

### Fix

Match the `Option` yourself and treat `None` as "input is gone, shut down." This is the pattern the skill recommends (`references/ecosystem-rust.md`, "Async with Tokio"):

```rust
let (tx, mut rx) = mpsc::unbounded_channel();
let stop = CancellationToken::new();
let input = spawn_input(tx, stop.clone()); // reader selects on stop.cancelled() too
let mut tick = tokio::time::interval(Duration::from_millis(250));

while !app.quit {
    tokio::select! {
        event = rx.recv() => match event {
            Some(event) => app.handle(event),
            None => break, // reader ended (EOF or error): stop instead of ticking with no input
        },
        _ = tick.tick() => app.on_tick(),
    }
}
stop.cancel();
input.await?;        // surfaces a reader panic as a JoinError instead of losing it
ratatui::restore();  // put the terminal back to normal
```

Other points:
- **Don't keep extra `tx` clones in the main task.** Otherwise `None` can never arrive. If workers need to send to the same channel, give them their own clones and make sure those clones drop too, or use a separate channel for app messages.
- **Report the failure.** If the reader stopped on an error, send the error through the channel before exiting (for example, an `AppEvent::InputError(e)` variant). Print it after `restore()` so the user learns why the app closed.
- **Cancel and await the reader before `restore()`** or before handing the terminal to a child process like `$EDITOR`. Then start a new reader with a new token. Otherwise the old `EventStream` keeps reading stdin and takes keystrokes meant for the child.
