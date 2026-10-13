The working directory is empty, so I couldn't look at your code. Everything below is from how Ratatui 0.30, Crossterm 0.29 and Tokio work, and I haven't compiled or run it.

## Why it breaks

- **Two programs read the same terminal input.** While Vim runs, your reader task is still calling `poll`/`read`. It takes Vim's keystrokes, and it also takes the replies to questions Vim asks the terminal at startup (version, cursor position, background colour). Vim then sees partial or stray bytes, which is the garbage you see at startup. When Vim exits, any late replies land in your reader and show up as fake key presses.
- **The nonzero exit probably skips cleanup.** Most likely the code does `status?`, or turns a nonzero exit into an `Err` and returns early. That return skips re-entering the TUI and restarting the reader, so the terminal stays in normal (cooked) mode with a stale screen.
- **Check for two copies of Crossterm.** If `Cargo.toml` pulls in a different Crossterm version than Ratatui uses (0.29 by default), you get two separate raw-mode states and two input readers. Use `ratatui::crossterm::*`.

## The ownership sequence

One owner, the main loop, holds both the `Terminal` and the reader's handle. Nothing else touches the terminal.

1. **Stop the reader and wait for it to finish.** Cancelling isn't enough: the old reader must not be inside `poll`/`read` when Vim starts.
2. **Leave the TUI**, undoing setup in reverse order: pop keyboard enhancement flags, disable bracketed paste and mouse capture, leave the alternate screen, show the cursor, disable raw mode, flush stdout.
3. **Throw away pending input**: discard Crossterm's internal buffer and call `tcflush(TCIFLUSH)` on stdin.
4. **Spawn Vim** with inherited stdio and wait for it. Its exit status is data, not an error.
5. **Always re-enter, whatever Vim's exit status:** flush input again (to drop Vim's late replies), enable raw mode, enter the alternate screen, turn your modes back on, hide the cursor, then call `terminal.clear()`. The clear is needed because Ratatui's diff buffer no longer matches what's on screen.
6. **Start a fresh reader**, then draw.

```rust
use std::{io, path::Path, process::ExitStatus, time::Duration};
use ratatui::{DefaultTerminal, crossterm::{cursor, event::{self, *}, execute, terminal::*}};
use tokio::{sync::mpsc, task::JoinHandle};
use tokio_util::sync::CancellationToken;

struct Input { cancel: CancellationToken, handle: JoinHandle<()> }

fn spawn_input(tx: mpsc::Sender<AppEvent>) -> Input {
    let cancel = CancellationToken::new();
    let c = cancel.clone();
    // poll with a timeout so cancellation is observed; a bare read() can't be interrupted
    let handle = tokio::task::spawn_blocking(move || {
        while !c.is_cancelled() {
            match event::poll(Duration::from_millis(50)) {
                Ok(true) => match event::read() {
                    Ok(ev) => if tx.blocking_send(AppEvent::Term(ev)).is_err() { break },
                    Err(e) => { let _ = tx.blocking_send(AppEvent::InputError(e)); break }
                },
                Ok(false) => {}
                Err(e) => { let _ = tx.blocking_send(AppEvent::InputError(e)); break }
            }
        }
    });
    Input { cancel, handle }
}

impl Input {
    async fn stop(self) { self.cancel.cancel(); let _ = self.handle.await; }
}

fn discard_input() {
    while matches!(event::poll(Duration::ZERO), Ok(true)) { let _ = event::read(); }
    unsafe { libc::tcflush(libc::STDIN_FILENO, libc::TCIFLUSH) };
}

fn leave_tui() -> io::Result<()> {
    execute!(io::stdout(), PopKeyboardEnhancementFlags, DisableBracketedPaste,
             DisableMouseCapture, LeaveAlternateScreen, cursor::Show)?;
    disable_raw_mode()?;
    discard_input();
    Ok(())
}

fn reenter_tui(terminal: &mut DefaultTerminal) -> io::Result<()> {
    discard_input(); // late replies to Vim's terminal queries
    enable_raw_mode()?;
    execute!(io::stdout(), EnterAlternateScreen, EnableMouseCapture, EnableBracketedPaste,
             PushKeyboardEnhancementFlags(KeyboardEnhancementFlags::DISAMBIGUATE_ESCAPE_CODES),
             cursor::Hide)?;
    terminal.clear()
}
```

## Keeping every outcome

Return all the outcomes instead of short-circuiting on the first failure:

```rust
pub struct EditorRun {
    pub leave: io::Result<()>,
    pub child: Option<io::Result<ExitStatus>>, // None = never spawned
    pub reenter: io::Result<()>,
}

async fn run_editor(terminal: &mut DefaultTerminal, input: &mut Option<Input>,
                    tx: &mpsc::Sender<AppEvent>, path: &Path,
                    shutdown: &CancellationToken) -> EditorRun {
    if let Some(i) = input.take() { i.stop().await; }
    let leave = leave_tui();
    let child = match &leave {
        Ok(()) => Some(run_child(path, shutdown).await),
        Err(_) => None,
    };
    let reenter = reenter_tui(terminal);          // runs no matter what happened above
    if reenter.is_ok() { *input = Some(spawn_input(tx.clone())); }
    EditorRun { leave, child, reenter }
}

#[derive(Debug, thiserror::Error)]
#[error("terminal re-entry failed after editor (editor result: {child:?})")]
pub struct ReentryFailed { pub child: Option<io::Result<ExitStatus>>, #[source] pub source: io::Error }
```

How the caller handles it:
- **Re-entry failed:** this is fatal. Call `ratatui::restore()` as a best effort, then return `ReentryFailed`. That error carries both Vim's result and the terminal error.
- **Re-entry worked:** the app keeps running. Show a nonzero exit or a spawn/leave error in the status line.

## Getting SIGTERM to shutdown

Have a signal task cancel a token. It must not touch the terminal or call `exit` itself. The main loop then breaks out and runs the normal restore path:

```rust
let shutdown = CancellationToken::new();
let s = shutdown.clone();
tokio::spawn(async move {
    use tokio::signal::unix::{signal, SignalKind};
    let (mut term, mut hup) = (signal(SignalKind::terminate()).unwrap(), signal(SignalKind::hangup()).unwrap());
    tokio::select! { _ = term.recv() => {}, _ = hup.recv() => {} }
    s.cancel();
});

loop {
    tokio::select! {
        _ = shutdown.cancelled() => break,
        Some(ev) = rx.recv() => { /* handle; may call run_editor */ }
    }
}
if let Some(i) = input.take() { i.stop().await; }
let _ = leave_tui(); // or ratatui::restore() plus undoing your extra modes
```

- **Installing the handler replaces the default.** Once Tokio handles SIGTERM, the process no longer dies on it, so the loop must actually watch the token.
- **SIGTERM while Vim is running:** forward SIGTERM to Vim, then reap it. Don't kill it.

```rust
async fn run_child(path: &Path, shutdown: &CancellationToken) -> io::Result<ExitStatus> {
    let mut child = tokio::process::Command::new("vim").arg(path).spawn()?; // inherits stdio; no kill_on_drop
    tokio::select! {
        st = child.wait() => st,
        _ = shutdown.cancelled() => {
            if let Some(pid) = child.id() { unsafe { libc::kill(pid as i32, libc::SIGTERM) }; }
            child.wait().await // Vim catches TERM, saves its swap file and restores the terminal itself
        }
    }
}
```

`run_editor` then re-enters as usual, the main loop sees the cancelled token, and normal teardown runs.

## The path that can't run cleanup

**SIGKILL (`kill -9`) can't run cleanup.** It can't be caught, so no `Drop`, panic hook, Tokio signal handler or restore code runs. The terminal stays in raw mode, on the alternate screen, with mouse reporting on, and the user has to run `reset` or `stty sane` themselves. SIGKILL can't be handled; you can only avoid causing it.

The same thing can happen to Vim through your own code. Tokio's `Child::kill()`, `start_kill()` and `kill_on_drop(true)` all send SIGKILL, so Vim dies without restoring its terminal state and leaves a swap file behind. That's why the code above uses `libc::kill(SIGTERM)`. It's also why `reenter_tui` resets everything and clears the screen instead of assuming Vim cleaned up.

`std::process::exit` and `abort` also skip `Drop`. The difference is that you control those calls, so you can restore the terminal before making them.
