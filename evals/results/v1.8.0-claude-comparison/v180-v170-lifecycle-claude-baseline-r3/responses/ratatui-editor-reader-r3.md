There's no code in the working directory, so this is a design answer with a sketch rather than a patch.

## Why it breaks

1. **Garbage at Vim startup:** your reader task is still reading stdin while Vim runs. It takes Vim's keystrokes and the terminal's replies to Vim's queries (cursor position, DA/XTVERSION, background color). Crossterm parses some of those, and the rest leak into Vim as text. Aborting the task doesn't fix this. A task blocked in `event::read()` inside `spawn_blocking` or a thread can't be aborted, so it keeps reading after you think it has stopped.
2. **Corrupted TUI afterward, especially on nonzero exit:** the code probably does `let status = cmd.status()?;` or treats a nonzero exit as an error. That `?` returns before raw mode and the alternate screen are re-entered. Even when re-entry does run, Ratatui's previous buffer still describes the screen from before Vim. The diff then only redraws the cells it thinks changed, and the rest keeps whatever Vim drew.

## Ownership sequence around the child

The rule: only one owner of the tty at a time, and every handover waits until it's finished.

```
1. Stop the reader and wait for it   cancel token → reader drops EventStream → reader_handle.await
2. Leave TUI mode                    pop keyboard flags, disable mouse/paste, show cursor,
                                     LeaveAlternateScreen, disable_raw_mode, flush
3. Run the child                     inherited stdio, wait for it; keep the result as a value, no `?`
4. Re-enter TUI mode                 ALWAYS, whatever step 3 returned:
                                     enable_raw_mode, EnterAlternateScreen, re-push flags/mouse/paste,
                                     hide cursor, terminal.clear()   ← forces a full redraw
5. (optional) Drain stale input      while event::poll(Duration::ZERO)? { event::read()?; }
6. Start a new reader                new EventStream in a new task
```

Make the reader cancellable. Use `EventStream` inside `select!` with a cancellation token, or a `poll(timeout)` loop that checks a stop flag. Don't use a bare blocking `read()`. Dropping `EventStream` wakes and stops crossterm's internal poll, so awaiting the task's `JoinHandle` really means nobody is reading stdin any more.

## Keeping both outcomes

Vim's result and the re-entry result are separate facts, so store both instead of letting one replace the other:

```rust
pub struct EditorOutcome {
    pub child: io::Result<ExitStatus>, // a nonzero exit is Ok(status), not an error
    pub reentry: io::Result<()>,
}

async fn run_editor(app: &mut App, path: &Path) -> EditorOutcome {
    app.stop_reader().await;                  // cancel + await JoinHandle
    if let Err(e) = leave_tui(&mut app.terminal) {
        // We never handed over, so don't launch Vim on a half-restored tty
        return EditorOutcome { child: Err(e), reentry: enter_tui(&mut app.terminal) };
    }

    let child = tokio::process::Command::new("vim").arg(path)
        .stdin(Stdio::inherit()).stdout(Stdio::inherit()).stderr(Stdio::inherit())
        .status().await;                      // no `?`

    let reentry = enter_tui(&mut app.terminal)
        .and_then(|()| app.terminal.clear()); // stale buffer → full repaint

    if reentry.is_ok() { app.start_reader(); }
    EditorOutcome { child, reentry }
}
```

The caller then handles the cases:
- **Re-entry failed:** the app can't keep running. Do a best-effort `ratatui::restore()` and go to shutdown. Report both errors, e.g. `"vim exited with {status:?}; could not restore terminal: {e}"`.
- **Re-entry worked but Vim failed** (spawn error or `!status.success()`): show it in the UI and carry on.

If you want an error type, use one variant that holds both, such as `Reentry { child: io::Result<ExitStatus>, source: io::Error }`, so neither error is dropped.

## SIGTERM → shutdown

- Register `tokio::signal::unix::signal(SignalKind::terminate())`, and SIGHUP too. Feed it into the same `CancellationToken` or channel that your main loop `select!`s on. Shutdown then goes through the normal path: stop the reader, `ratatui::restore()` (or your own `leave_tui`), and return from `main` so destructors run.
- Once you register a handler, Tokio replaces the default action. If nothing listens, SIGTERM is silently ignored, so it must actually be wired to shutdown.
- **While Vim is running:** SIGTERM sent to your PID alone doesn't reach Vim. In `run_editor`, `select!` on `child.wait()` and the shutdown token. When shutdown fires, forward SIGTERM to the child (`nix::sys::signal::kill(Pid::from_raw(child.id()? as i32), SIGTERM)`) and wait for it to exit. Then skip step 4: the tty is already in cooked mode, so just exit.
- In raw mode, Ctrl-C arrives as a key event, not SIGINT. Handle it in the event loop.
- `ratatui::init()` in 0.30 installs a panic hook that restores the terminal. That hook runs even with `panic = "abort"`, so panics are covered.

## The path that can't clean up

**SIGKILL** (and SIGSTOP, which suspends rather than ends) can't be caught, blocked or handled. The kernel removes the process, so no handler, `Drop` or panic hook runs. The terminal stays in raw mode on the alternate screen, and the user has to run `reset` or `stty sane`.

`std::process::exit` and `std::process::abort` also skip destructors, but those are calls your own code makes. You can restore the terminal before calling them, which isn't possible with SIGKILL.
