## Why Vim starts with garbage and the TUI breaks afterward

There are two separate bugs.

1. **Your reader task is still running while Vim runs.** It competes with Vim for stdin. Your app swallows some keystrokes, and it also swallows the replies Vim gets back from the terminal when it asks about the terminal (for example, its background-color query). The leftover bytes show up as garbage in Vim. Cancelling the task isn't enough: you also have to **wait for it to finish**, so its `EventStream` has been dropped before you hand the terminal over.
2. **A nonzero Vim exit skips re-entry.** If anything between `restore()` and re-entry uses `?`, or turns a nonzero exit into an error, the function returns early. Raw mode and the alternate screen never come back, and Ratatui keeps drawing as if they had. A nonzero `ExitStatus` is a normal value: show it to the user and never return early on it.

Also run `cargo tree -p crossterm`. If two Crossterm versions are in the build, you have two event readers, and stopping one doesn't stop the other.

## The ownership sequence

1. Cancel the reader token and **await** its `JoinHandle`. Discard any events still queued in the channel; they were meant for the TUI.
2. Turn off any modes you enabled yourself, such as mouse capture, bracketed paste or keyboard enhancement. Then call `ratatui::restore()`.
3. Spawn Vim and wait for it. Keep the result; don't use `?` on it.
4. Re-enter whether or not Vim succeeded: enable raw mode, enter the alternate screen, call `terminal.clear()`, and turn your extra modes back on.
5. Start a **new** reader with a **new** token.
6. Call `app.reload()`, because Vim may have changed the file. Then draw. `clear()` makes that draw repaint every cell.

```rust
use std::{fmt, io, process::ExitStatus};
use nix::{sys::signal::{kill, Signal as Sig}, unistd::Pid};
use ratatui::{DefaultTerminal, crossterm::{execute, event::Event,
    terminal::{enable_raw_mode, EnterAlternateScreen}}};
use tokio::{process::Command, signal::unix::Signal, sync::mpsc, task::JoinHandle};
use tokio_util::sync::CancellationToken;

pub struct Input { stop: CancellationToken, task: JoinHandle<()> }

impl Input {
    pub fn start(tx: mpsc::UnboundedSender<Event>) -> Self {
        let stop = CancellationToken::new();
        let task = spawn_input(tx, stop.clone());       // the EventStream select! loop
        Self { stop, task }
    }
    pub async fn stop(self) {
        self.stop.cancel();
        let _ = self.task.await;                        // EventStream is dropped here
    }
}

pub enum Handoff {
    Resumed(io::Result<ExitStatus>),                    // nonzero status is Ok(status)
    Shutdown,                                           // SIGTERM arrived during the child
}

#[derive(Debug)]
pub struct ReentryFailed { pub child: io::Result<ExitStatus>, pub reentry: io::Error }

impl fmt::Display for ReentryFailed {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "terminal re-entry failed: {}; editor result: {:?}", self.reentry, self.child)
    }
}
impl std::error::Error for ReentryFailed {}

pub async fn run_editor(
    terminal: &mut DefaultTerminal,
    app: &mut App,
    input: &mut Option<Input>,
    tx: &mpsc::UnboundedSender<Event>,
    rx: &mut mpsc::UnboundedReceiver<Event>,
    sigterm: &mut Signal,
) -> Result<Handoff, ReentryFailed> {
    if let Some(reader) = input.take() { reader.stop().await; }
    while rx.try_recv().is_ok() {}
    ratatui::restore();                                 // disable your own mouse/paste modes first

    let child = match Command::new("vim").arg(&app.path).spawn() {
        Err(e) => Err(e),
        Ok(mut vim) => tokio::select! {
            status = vim.wait() => status,
            _ = sigterm.recv() => {
                if let Some(pid) = vim.id() { let _ = kill(Pid::from_raw(pid as i32), Sig::SIGTERM); }
                let _ = vim.wait().await;
                return Ok(Handoff::Shutdown);           // terminal is already shell-facing
            }
        },
    };

    let reentry = enable_raw_mode()
        .and_then(|()| execute!(io::stdout(), EnterAlternateScreen))
        .and_then(|()| terminal.clear());
    if let Err(reentry) = reentry {
        return Err(ReentryFailed { child, reentry });
    }

    *input = Some(Input::start(tx.clone()));
    app.reload();
    let _ = terminal.draw(|f| app.draw(f));            // a draw error surfaces on the next loop pass
    Ok(Handoff::Resumed(child))
}
```

## Keeping both results

- **Vim fails, re-entry succeeds:** you get `Resumed(Err(e))` or `Resumed(Ok(status))` with a nonzero status. The TUI keeps running. Show the problem in the status line, for example `vim exited 1` or `couldn't launch vim: …`.
- **Re-entry fails:** you get `ReentryFailed { child, reentry }`, which carries **both** results. Don't keep drawing, because the terminal is in an unknown state. Re-entry isn't all-or-nothing: raw mode might be on even though entering the alternate screen failed. So clean up step by step on a best-effort basis: call `ratatui::restore()`, show the cursor, and turn off your extra modes. Then exit, reporting both results.
- **The underlying rule:** don't combine the two results until both exist. Only then match on them; never use `?` on Vim's result before re-entry.

## Getting SIGTERM to shutdown

Ratatui doesn't turn signals into events. You have to deliver SIGTERM to your loop as a quit request:

```rust
let mut sigterm = tokio::signal::unix::signal(SignalKind::terminate())?; // before ratatui::init()
let mut terminal = ratatui::init();
let result = async {
    while !app.should_quit {
        terminal.draw(|f| app.draw(f))?;
        tokio::select! {
            ev = rx.recv()        => match ev { Some(ev) => app.handle(ev), None => break },
            _  = sigterm.recv()   => app.should_quit = true,
            _  = tick.tick()      => app.on_tick(),
        }
        // run_editor(...) is called from here when the user asks for it;
        // Handoff::Shutdown sets should_quit, ReentryFailed breaks with the error
    }
    Ok::<_, color_eyre::Report>(())
}.await;
if let Some(reader) = input.take() { reader.stop().await; }
ratatui::restore();
result
```

- **Register the handler first.** Until you create the handler, SIGTERM still has its default behavior: it kills the process immediately, and no Rust cleanup runs.
- **During the handoff**, your main loop isn't running, so `run_editor` listens for the same signal and forwards SIGTERM to Vim. `kill <pid>` only reaches your process, not Vim. The terminal is already restored at that point, so return `Shutdown` and don't re-enter. Calling `ratatui::restore()` again at shutdown is safe.
- **Ctrl+C is not a signal here.** In raw mode it arrives as a key press, so bind it to quit. While Vim is running, Ctrl+C belongs to Vim.

## The path that can't clean up

**SIGKILL (`kill -9`) can't be caught.** No handler, `Drop`, panic hook, or `restore()` runs. If it hits while your TUI owns the terminal, the shell is left in raw mode on the alternate screen, and the only fix is for the user to run `reset` or `stty sane`.

Two related cases:
- **Any SIGTERM before your handler is registered** also skips cleanup, which is why you register it first.
- **`std::process::exit` skips destructors.** So does `panic = "abort"`, although Ratatui's panic hook still restores the terminal before the abort.

**What to test:** in a PTY, run four cases: Vim exits 0, Vim exits 1 (`:cq`), Vim can't be found (spawn error), and you send SIGTERM to your app while Vim is open. In each case, check that afterward the shell is in cooked mode with a visible cursor, or that the TUI repainted correctly. Also make re-entry fail on purpose to confirm that both results get reported.
