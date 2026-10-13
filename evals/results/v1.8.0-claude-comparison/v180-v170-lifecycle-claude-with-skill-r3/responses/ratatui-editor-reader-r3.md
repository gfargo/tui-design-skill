Your symptoms come from two problems:

- **Garbage when Vim starts:** your Crossterm `EventStream` task is still reading stdin while Vim runs. It steals Vim's keystrokes and the terminal's replies to Vim's capability queries, so Vim starts with partial input.
- **Corrupted TUI afterward:** something in your handoff returns early, often a `?` or a `!status.success()` check, before the code that re-enters raw mode and the alternate screen. A nonzero exit from Vim is still `Ok(ExitStatus)`, not an `Err`, so it must never skip re-entry.

## 1. Ownership sequence around the child

Each step must finish before the next one starts:

1. **Stop input.** Cancel the reader's token and **await its `JoinHandle`**. Cancelling alone doesn't guarantee the task has stopped reading.
2. **Restore the terminal** with `ratatui::restore()` (leaves raw mode and the alternate screen, shows the cursor).
3. **Run Vim and wait for it.** Keep the `Result` in a variable; don't apply `?` yet.
4. **Re-enter:** `enable_raw_mode` → `EnterAlternateScreen` → `terminal.clear()`, so the next draw repaints every cell.
5. **Start a fresh reader** with a new `CancellationToken`. A cancelled token can't be reused.
6. **Reload** anything Vim may have changed. A redraw only repaints your current model; it doesn't fetch new data.
7. **Redraw.**

```rust
use std::{io::stdout, process::ExitStatus};
use ratatui::crossterm::{execute, terminal::{enable_raw_mode, EnterAlternateScreen}};
use color_eyre::eyre::eyre;

struct Input {
    tx: mpsc::UnboundedSender<Event>,
    stop: CancellationToken,
    task: Option<JoinHandle<()>>,
}

impl Input {
    async fn stop(&mut self) {
        self.stop.cancel();
        if let Some(task) = self.task.take() {
            let _ = task.await; // the reader is really gone, not just asked to leave
        }
    }
    fn start(&mut self) {
        self.stop = CancellationToken::new(); // a cancelled token can't be reused
        self.task = Some(spawn_input(self.tx.clone(), self.stop.clone()));
    }
}

async fn run_editor(terminal: &mut DefaultTerminal, app: &mut App) -> Result<ExitStatus> {
    app.input.stop().await;
    ratatui::restore();

    // Keep the outcome; a nonzero exit is still Ok(status)
    let child = tokio::process::Command::new("vim").arg(&app.path).status().await;

    let reentry = enable_raw_mode()
        .and_then(|()| execute!(stdout(), EnterAlternateScreen))
        .and_then(|()| terminal.clear());

    match (child, reentry) {
        (Ok(status), Ok(())) => {
            app.input.start();
            app.reload();
            terminal.draw(|f| app.draw(f))?;
            Ok(status) // the caller decides what a nonzero status means
        }
        (child, reentry) => Err(eyre!("editor: {child:?}; terminal re-entry: {reentry:?}")),
    }
}
```

Use `tokio::process::Command` (or `spawn_blocking`) so waiting for Vim doesn't block a runtime worker thread. Ratatui's official recipe uses `std::process::Command`, which works but blocks the thread. Both forms inherit stdin, stdout and stderr by default, which is what Vim needs.

## 2. Keeping both outcomes when Vim and re-entry both fail

- **Keep both results as values** and match on the pair, as above. A `?` on the first one throws away the second, and because the child runs first, that `?` is usually what skips re-entry.
- **Report a nonzero Vim exit as a status, not an error.** Show something like "editor exited 1" in the UI and keep running.
- **Re-entry isn't all-or-nothing.** Raw mode might be on while the alternate screen isn't. When it fails, don't restart the reader and don't draw. Return the combined error and let your outer `ratatui::run` / `restore()` path do final teardown. If you use the fallible `try_*` helpers, make each cleanup step a separate best-effort attempt (raw mode off, leave alternate screen, disable mouse/paste, show cursor). One `Err` doesn't mean the earlier steps were undone.
- **A successful redraw** only shows the renderer recovered. It doesn't prove the edited data is valid.

## 3. How SIGTERM should reach shutdown

Ratatui doesn't turn signals into events. Make SIGTERM another input to your existing `select!` loop, so it leaves through the same cleanup as `q`:

```rust
let mut term = tokio::signal::unix::signal(SignalKind::terminate())?;
while !app.should_quit {
    terminal.draw(|f| app.draw(f))?;
    tokio::select! {
        event = rx.recv() => match event { Some(e) => app.handle(e), None => break },
        _ = term.recv() => app.should_quit = true,
        _ = tick.tick() => app.on_tick(),
    }
}
app.input.stop().await; // cancel + await before the final restore
// return here; ratatui::run (or your restore() after the loop) does the teardown
```

- **Don't call `restore()` or `exit()` inside a signal handler or a separate task.** The handler only requests shutdown; the loop owns teardown.
- **Once you register the handler, Tokio replaces the default "terminate" behaviour for the life of the process.** If the loop doesn't act on it, SIGTERM is effectively ignored.
- **A SIGTERM that arrives while Vim is running** waits in the stream and gets handled when control returns to the loop after re-entry. That's correct: you shut down from a known terminal state.
- **Ctrl+C is not SIGINT in raw mode.** It arrives as a key event, so handle it in `app.handle`.
- **Windows has no SIGTERM.** Use `tokio::signal::ctrl_c` or the `tokio::signal::windows` close and shutdown events there.

## 4. Hard-termination paths that can't run cleanup

- **SIGKILL (`kill -9`)** can't be caught, blocked or handled. No destructor, panic hook or `restore()` runs, and the terminal stays in raw mode on the alternate screen.
- **SIGTERM with no registered handler** also kills the process without unwinding Rust code. That's why step 3 matters.
- **`std::process::exit` and `abort` called inside the app** skip destructors too. With `panic = "abort"`, Ratatui's panic hook still runs before the abort, but `Drop`-based cleanup doesn't.

After any of these, the user's shell has to be fixed from outside, for example by running `reset` (or `stty sane`) in that terminal.

## Verify

Run in a real PTY: Vim `:q`, Vim `:cq` (nonzero exit), Vim missing from `PATH` (spawn error), re-entry failure injected after Vim exits, `kill -TERM <pid>` while idle and while Vim is open, and a panic. After each one, check that the shell is in cooked mode, the cursor is visible, and you're back on the main screen.
