The garbage comes from your input task. It keeps reading stdin while Vim runs, so it steals Vim's keystrokes and the replies Vim gets back from the terminal. The corruption afterward comes from returning early: if a `?` on Vim's result fires before the terminal is set up again, the TUI is never re-entered and redrawn.

A nonzero exit from Vim is not an `Err`. `Command::status()` returns `Ok(status)` with a nonzero code. You only get `Err` when Vim can't be spawned or waited on. Neither case should skip re-entry.

## 1. Ownership sequence around the child

Stopping the reader means cancelling it and then **awaiting its `JoinHandle`**. Cancelling alone isn't enough, because `EventStream` may still be reading until the task has actually finished and dropped it.

1. Cancel the input task's token and `await` its `JoinHandle`.
2. Call `ratatui::restore()`. This turns off raw mode, leaves the alternate screen and shows the cursor.
3. Spawn Vim and wait for it. Store the result and don't use `?` on it.
4. Re-enter: turn raw mode on, enter the alternate screen, then `terminal.clear()` so the next draw repaints every cell.
5. Start a new input task with a **new** `CancellationToken`. A cancelled token stays cancelled.
6. Reload any data Vim may have changed. A redraw only repaints what's already in memory.
7. Combine both results, and redraw only if re-entry worked.

```rust
use std::{io::stdout, process::ExitStatus};
use ratatui::crossterm::{execute, terminal::{enable_raw_mode, EnterAlternateScreen}};
use color_eyre::eyre::{eyre, Result};

async fn run_editor(terminal: &mut DefaultTerminal, app: &mut App) -> Result<ExitStatus> {
    app.input.stop().await;                 // stop.cancel(); handle.await — reader is gone
    ratatui::restore();

    // Async wait so the runtime isn't blocked; the child inherits the tty.
    let child = tokio::process::Command::new("vim").arg(&app.path).status().await; // no `?`

    let reentry = enable_raw_mode()
        .and_then(|()| execute!(stdout(), EnterAlternateScreen))
        .and_then(|()| terminal.clear());

    app.input.start();                      // fresh EventStream task + new token
    app.reload();

    match (child, reentry) {
        (Ok(status), Ok(())) => {
            terminal.draw(|f| app.draw(f))?;
            Ok(status)                      // caller shows "vim exited 1" in the status bar
        }
        (child, reentry) => Err(eyre!("child: {child:?}; reentry: {reentry:?}")),
    }
}
```

The caller decides what a nonzero `status` means for the user, such as a status-line message or discarding the edit. It's never a reason to skip re-entry.

## 2. Keeping both failures

- **Don't use `?` until both results exist.** Store `child` and `reentry`, then match on the pair. If both fail, report both. A `?` on either one would discard the other.
- **Re-entry is not all-or-nothing.** If raw mode turns on but entering the alternate screen fails, the terminal is left half set up. If `reentry` is `Err`, assume you can't draw. Do a best-effort cleanup with separate calls, ignoring each call's error: disable raw mode, leave the alternate screen, turn off mouse and paste modes, show the cursor. Then return the combined error.
- A successful redraw only shows that the renderer recovered. It doesn't show that Vim's work succeeded, so check `status` separately.

## 3. Getting SIGTERM to shutdown

Ratatui doesn't turn signals into events. Make SIGTERM one more branch in the main `select!`, so it leaves through the same exit path as `q`:

```rust
use tokio::signal::unix::{signal, SignalKind};

let mut term = signal(SignalKind::terminate())?;   // installs a handler; default disposition no longer applies
while !app.should_quit {
    terminal.draw(|f| app.draw(f))?;
    tokio::select! {
        ev = rx.recv() => match ev { Some(e) => app.handle(e), None => break },
        _ = tick.tick() => app.on_tick(),
        _ = term.recv() => app.should_quit = true,
    }
}
app.input.stop().await;    // cancel + await the reader before restoring
// then return through ratatui::run / ratatui::restore() — keep the loop result, restore, return it
```

Don't call `restore()` or `process::exit` inside the signal branch. Set the quit flag, let the loop end, and let the normal cleanup run. If SIGTERM arrives while Vim is running, your process is waiting on the child. Either forward the signal to Vim or let the wait finish; the handoff still has to re-enter or restore before you exit. On Windows, SIGTERM doesn't exist, so put this branch behind `#[cfg(unix)]`.

## 4. The termination path that can't clean up

**SIGKILL.** It can't be caught or handled, so no Rust code runs: no destructors, no panic hook, no `restore()`. The user is left in raw mode on the alternate screen and has to run `reset`.

The same applies to **SIGTERM with no handler installed**. Its default action kills the process without unwinding. That's why the `signal(SignalKind::terminate())` handler above must be installed before you rely on graceful shutdown.

(`std::process::exit` and `abort` also skip destructors, so don't use them to quit the TUI.)

To check this, run it in a PTY. Have Vim exit with `:cq` (nonzero) and confirm the TUI redraws. Send SIGTERM both while idle and while Vim is open, and confirm the shell comes back clean. Force a re-entry failure and confirm the error mentions both the child and re-entry.
