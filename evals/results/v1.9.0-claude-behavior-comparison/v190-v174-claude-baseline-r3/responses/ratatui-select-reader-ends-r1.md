## Short answer: the app keeps running but stops responding to input

You can't quit with a keypress, and the terminal stays in raw mode / the alternate screen. It doesn't panic and doesn't spin the CPU. From the user's side it looks frozen, except that anything driven by `on_tick` keeps updating.

## Why

1. When the reader task ends, its `Sender` is dropped. If that was the last sender, `rx.recv()` starts returning `None` right away, every time it's called.
2. In `tokio::select!`, if a branch's pattern doesn't match (`Some(event)` vs `None`), that branch is **disabled for that call** of `select!` and it waits on the remaining branches.
3. `tick.tick()` is never disabled, so `select!` just waits for the next tick.
4. Next loop iteration, `select!` runs again, `recv()` gives `None` again, the branch is disabled again, and it waits on the tick again. This repeats forever.

So `app.handle` is never called again, `app.quit` never becomes `true`, and the loop never ends. Ctrl-C won't help either if your key handler is what sets `quit`, because raw mode stops Ctrl-C from sending SIGINT.

Related cases:
- **You still hold a `tx` clone somewhere** (for example, you pass it to other tasks or keep it on `App`): `recv()` never returns `None`. It just stays pending. You get the same symptom, but now nothing in the code can even detect it.
- **The reader panicked:** Tokio catches the panic, and unless you `.await` the `JoinHandle` nobody sees it. The panic message goes to stderr while you're in the alternate screen, so it either garbles the display or disappears.
- **No always-ready branch:** if every branch were disabled, `select!` would panic with "all branches are disabled and there is no else branch". Your tick branch is what prevents that, and it's also what turns the failure into a silent hang.

A common way for the reader to exit is a loop like `while let Some(Ok(ev)) = stream.next().await`, which quietly stops on the first `Err`.

## Fix

Handle `None` explicitly:

```rust
loop {
    tokio::select! {
        maybe = rx.recv() => match maybe {
            Some(event) => app.handle(event),
            None => break, // or: return Err(anyhow!("input reader stopped"))
        },
        _ = tick.tick() => app.on_tick(),
    }
    if app.quit { break }
}
```

It's also worth doing these:
- **Find out why the reader died.** Keep its `JoinHandle` and add it as a `select!` branch (`res = &mut reader => ...`), or have the reader send an `Event::Error(e)` before it returns instead of failing silently.
- **Always restore the terminal.** Use a guard type whose `Drop` calls `disable_raw_mode` and `LeaveAlternateScreen`, plus a panic hook that does the same. Then any exit path, including panics and early `return`s, leaves the shell usable. `ratatui::init()` / `ratatui::restore()` install a hook like this for you.
- **Don't keep extra `tx` clones** on the receiving side if you want closing the channel to work as a shutdown signal.
