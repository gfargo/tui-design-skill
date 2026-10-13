There's no project code in the working directory, so this answer is based on how Ratatui 0.30, Crossterm and Tokio behave, not on your code. I haven't compiled the code below.

## Why it breaks

- **Garbage in Vim:** your reader task is still reading the terminal while Vim runs, so it takes some of Vim's keystrokes and replies to terminal queries. Any modes you left on (mouse capture, bracketed paste, kitty keyboard flags) also send escape sequences that Vim shows as text.
- **Corrupted TUI afterward:** Ratatui only redraws cells that changed since its last frame. After Vim has painted the screen, that saved frame is wrong, so you need `terminal.clear()`. The "worse when Vim exits nonzero" pattern almost always means a `?` or early return on a failed exit status skips the re-entry code.

## Ownership sequence

Only one thing should read the terminal at a time, and every handoff must be confirmed before the next step:

1. **Stop the reader and wait for it.** Cancel it, then `.await` its `JoinHandle` so the `EventStream` has been dropped. Cancelling alone isn't enough.
2. **Leave TUI mode,** undoing setup in reverse: disable mouse capture, disable bracketed paste, pop keyboard flags, show the cursor, leave the alternate screen, `disable_raw_mode`.
3. **Run Vim** with inherited stdio using `tokio::process`, not a blocking `std::process` call. Store the result; don't use `?` on it.
4. **Re-enter, even if step 3 failed:** `enable_raw_mode`, enter the alternate screen and re-enable your modes, **discard queued input**, then `terminal.clear()`.
5. **Start a new reader** with a fresh `EventStream`.

```rust
use ratatui::crossterm::{
    event::{self, DisableBracketedPaste, DisableMouseCapture, EventStream},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
    cursor::{Hide, Show},
};
use tokio_util::sync::CancellationToken;

struct InputTask { stop: CancellationToken, handle: tokio::task::JoinHandle<()> }

impl InputTask {
    fn spawn(tx: tokio::sync::mpsc::Sender<event::Event>) -> Self {
        let stop = CancellationToken::new();
        let s = stop.clone();
        let handle = tokio::spawn(async move {
            let mut events = EventStream::new();
            loop {
                tokio::select! {
                    biased;
                    _ = s.cancelled() => break,
                    ev = events.next() => match ev {
                        Some(Ok(e)) => if tx.send(e).await.is_err() { break },
                        _ => break,
                    },
                }
            }
            // `events` is dropped here; the reader no longer owns the terminal
        });
        Self { stop, handle }
    }

    async fn stop(self) {
        self.stop.cancel();
        let _ = self.handle.await;
    }
}
```

Caveat: dropping `EventStream` tells its helper thread to stop but doesn't wait for the thread to exit. If you see stolen keystrokes even with this in place, run your own reader on a dedicated thread (`event::poll(timeout)` + `read`, with a stop flag) and wait for that thread to finish.

## Keeping both failures

The Vim result and the re-entry result are separate failures, and one doesn't cause the other. Return both instead of letting either hide the other:

```rust
pub enum ChildEnd { Exited(ExitStatus), Shutdown(Option<ExitStatus>) }

pub struct EditorOutcome {
    pub child: io::Result<ChildEnd>,   // includes "failed to leave TUI / spawn"
    pub resume: Option<io::Result<()>>, // None = skipped because we're shutting down
}

async fn run_editor(
    terminal: &mut DefaultTerminal,
    input: &mut Option<InputTask>,
    path: &Path,
    shutdown: &CancellationToken,
) -> EditorOutcome {
    if let Some(t) = input.take() { t.stop().await; }

    let child = match leave_tui() {
        Ok(()) => run_child(path, shutdown).await,
        Err(e) => Err(e),
    };

    let resume = match child {
        Ok(ChildEnd::Shutdown(_)) => None,
        _ => Some(enter_tui(terminal)), // runs on Ok, nonzero exit, AND Err
    };
    EditorOutcome { child, resume }
}

fn leave_tui() -> io::Result<()> {
    // undo only what you enabled; run every step, keep the first error
    let a = execute!(io::stdout(), DisableMouseCapture, DisableBracketedPaste, Show, LeaveAlternateScreen);
    let b = disable_raw_mode();
    a.and(b)
}

fn enter_tui(terminal: &mut DefaultTerminal) -> io::Result<()> {
    enable_raw_mode()?;
    execute!(io::stdout(), EnterAlternateScreen, Hide /*, EnableMouseCapture, ... */)?;
    while event::poll(Duration::ZERO)? { let _ = event::read()?; } // stale input typed while Vim ran
    terminal.clear() // Ratatui's saved frame is out of date; force a full redraw
}
```

What the caller does:

- **Re-entry failed:** the TUI can't continue. Call `ratatui::try_restore()` as a best effort, print **both** errors to stderr, and exit nonzero.
- **Re-entry worked:** restart `InputTask`. Show a nonzero exit or a spawn error in the UI; it isn't fatal.

## How SIGTERM should reach shutdown

A signal should only set a flag. The normal shutdown code then does the cleanup.

```rust
let shutdown = CancellationToken::new();
{
    use tokio::signal::unix::{signal, SignalKind};
    let mut term = signal(SignalKind::terminate())?;  // register BEFORE ratatui::init()
    let mut hup  = signal(SignalKind::hangup())?;
    let tok = shutdown.clone();
    tokio::spawn(async move {
        tokio::select! { _ = term.recv() => {}, _ = hup.recv() => {} }
        tok.cancel();
    });
}
// main loop: select! { _ = shutdown.cancelled() => break, ev = rx.recv() => ..., }
// after loop: stop InputTask, then ratatui::restore()
```

- **Register before entering raw mode.** That way there's no moment where the default SIGTERM action kills you while the terminal is raw.
- **Your loop must watch the token.** Once Tokio installs a handler, SIGTERM no longer terminates the process by default. If nothing checks the token, SIGTERM does nothing.
- **Never restore the terminal from inside the signal handler.**
- **SIGTERM while Vim is running.** `kill <pid>` only reaches you, so pass it on to Vim:

```rust
async fn run_child(path: &Path, shutdown: &CancellationToken) -> io::Result<ChildEnd> {
    let mut child = tokio::process::Command::new("vim").arg(path).spawn()?;
    tokio::select! {
        st = child.wait() => Ok(ChildEnd::Exited(st?)),
        _ = shutdown.cancelled() => {
            if let Some(pid) = child.id() {
                let _ = nix::sys::signal::kill(nix::unistd::Pid::from_raw(pid as i32),
                                               nix::sys::signal::Signal::SIGTERM);
            }
            match tokio::time::timeout(Duration::from_secs(5), child.wait()).await {
                Ok(st) => Ok(ChildEnd::Shutdown(st.ok())),
                Err(_) => { child.kill().await?; Ok(ChildEnd::Shutdown(None)) } // last resort
            }
        }
    }
}
```

On shutdown, skip re-entering the TUI. You're already out of raw mode, and the final `ratatui::restore()` is harmless if repeated.

Don't use `child.kill()` or `kill_on_drop(true)` as your first move: Tokio sends **SIGKILL**, so Vim gets no chance to restore the terminal. Use them only after the timeout, as above. Because your process is still alive, you can reset the terminal yourself afterward.

## The path that can't run cleanup

**SIGKILL (`kill -9`) sent to your process.** It can't be caught, so no handler, `Drop`, panic hook or Tokio task runs. The terminal stays in raw mode, on the alternate screen, with mouse reporting on. The only fix is outside your program: `reset` or `stty sane` in the shell.

Two in-process exits also skip `Drop`-based cleanup:
- **`std::process::exit`:** call `ratatui::restore()` explicitly before it.
- **`panic = "abort"`:** the panic hook installed by `ratatui::init()` still runs, but `Drop` guards don't.
