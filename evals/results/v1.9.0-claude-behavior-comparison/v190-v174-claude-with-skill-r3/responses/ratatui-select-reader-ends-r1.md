**Your app stops taking input but keeps running, so the user can't quit it.**

Here's why:

1. When the reader task exits (EOF, an `Err` from `EventStream`, or a panic), its `Sender` is dropped. Every later `rx.recv()` returns `None` straight away.
2. `None` doesn't match the pattern `Some(event) = rx.recv()`. In `tokio::select!`, a branch whose pattern doesn't match is **disabled** for that call. It doesn't break the loop and it doesn't panic.
3. `select!` then waits on the only branch left, `tick.tick()`. So `on_tick()` keeps firing every interval. On the next iteration `recv()` returns `None` again, the branch is disabled again, and it goes back to waiting on the tick.

What the user sees:

- **No CPU spin.** The tick paces the loop, so it looks healthy from outside.
- **No key presses get through, ever.** That includes your quit key. In raw mode Ctrl-C is just a key event, not SIGINT, so it's lost too. `app.quit` can never become true from input.
- **The terminal stays in raw mode / alternate screen.** The user has to kill the process from another shell, and their terminal is left broken. They'll probably need to run `reset`.
- **A panic in the reader is silently swallowed** if nothing ever awaits its `JoinHandle`.

Without the tick branch it would fail loudly: `select!` panics when every branch is disabled and there's no `else`. The tick is what turns the failure into a silent hang.

## Fix

Match `None` explicitly, and keep the reader's handle so you can see why it died:

```rust
let (tx, mut rx) = mpsc::unbounded_channel();
let stop = CancellationToken::new();
let input = spawn_input(tx, stop.clone()); // JoinHandle<()>
let mut tick = tokio::time::interval(Duration::from_millis(250));

while !app.quit {
    tokio::select! {
        event = rx.recv() => match event {
            Some(event) => app.handle(event),
            None => break, // reader ended (EOF/error/panic): stop instead of ticking with no input
        },
        _ = tick.tick() => app.on_tick(),
    }
}
stop.cancel();
input.await?; // surfaces a reader panic as a JoinError instead of losing it
// then ratatui::restore()
```

Related points:

- **Reader side:** have it `break` on `Some(Err(_))` or `None` from `EventStream` rather than retrying forever. Then the main loop's `None => break` handles every way the reader can end. Give it a `CancellationToken` so you can stop it on purpose before `ratatui::restore()` or before handing the terminal to a child process like `$EDITOR`.
- **Restore on every exit path:** break out normally, or install a panic hook that restores the terminal (`ratatui::init()` does this for you). That way a failed reader never leaves the user's shell in raw mode.
- **Optional:** if you'd rather show an error than quit, set `app.error = Some("input closed")`, draw once, then exit. Just don't keep looping: no input means the user can't do anything.

The skill's Rust reference (`references/ecosystem-rust.md`, section "Async with Tokio") uses this same pattern, including the `None => break` arm.
