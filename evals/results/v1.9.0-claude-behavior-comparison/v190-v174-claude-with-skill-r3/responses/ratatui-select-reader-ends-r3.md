The app freezes. It keeps running and ticking, but it never receives another key press, so the user can't quit it from the keyboard.

**What happens step by step**

1. When the reader task exits (for example, `EventStream` returns an error or `None`, or the task panics), its `Sender` is dropped.
2. If that was the only `Sender`, every call to `rx.recv()` now returns `None` immediately.
3. Your branch pattern is `Some(event) = rx.recv()`. In `tokio::select!`, a value that doesn't match the pattern disables that branch for the current `select!` call. It doesn't break the loop.
4. Only `tick.tick()` is left, so the loop waits for the tick, runs `app.on_tick()`, checks `app.quit` (which is still false) and loops again.
5. The next `select!` polls `recv()` again, gets `None` again, disables the branch again and waits on the tick again. This repeats forever.

**What the user sees**

- **The app can't be quit.** Raw mode turns off the terminal's signal handling, so Ctrl+C arrives as an ordinary key event, and nothing reads key events anymore. `app.quit` can never become true.
- **It doesn't hog the CPU.** The tick interval paces the loop, so it looks like a normal, idle app. That makes it harder to notice.
- **The terminal is left broken.** The user has to kill the process from another terminal. Your restore code never runs, so the shell is left in raw mode and the alternate screen, and they have to run `reset`.
- **The cause is hidden.** Nothing checks the reader's `JoinHandle`, so a panic or I/O error in the reader is never reported.

Two related cases:
- If something else still holds a clone of `tx` (for example, background workers sending app messages on the same channel), `recv()` never returns `None`. It just waits forever. The result is the same frozen app, and checking for `None` won't catch it.
- If you remove the tick branch, `select!` panics once every branch is disabled, because it has no `else` branch. The panic hook, if you have one, then restores the terminal, so ironically that version fails more cleanly.

**Fix**

Bind the result of `recv()` without a pattern and handle `None` yourself. Also give the reader a way to be stopped, and wait for it to finish. This is the pattern the skill recommends (`references/ecosystem-rust.md`, "Async with Tokio"):

```rust
let (tx, mut rx) = mpsc::unbounded_channel();
let stop = CancellationToken::new();
let input = spawn_input(tx, stop.clone()); // EventStream reader that selects on stop.cancelled()

while !app.quit {
    tokio::select! {
        event = rx.recv() => match event {
            Some(event) => app.handle(event),
            None => break, // reader ended (EOF or error); stop instead of ticking with no input
        },
        _ = tick.tick() => app.on_tick(),
    }
}
stop.cancel();
input.await?; // reports a reader panic instead of losing it
```

Further steps, depending on your setup:
- **If other code shares the sender:** watch the reader directly by adding a `res = &mut input => …` branch to the `select!`. Then you notice it exiting even when `None` never arrives.
- **Restore the terminal on every exit path:** use a drop guard or `ratatui::restore()` in a panic hook, so even an unexpected exit leaves a usable shell.
- **Before a child process takes over the terminal:** cancel the reader and wait for it to finish before launching something like `$EDITOR`. Afterwards, start a new reader with a new token. Otherwise the old `EventStream` competes with the child for stdin.
