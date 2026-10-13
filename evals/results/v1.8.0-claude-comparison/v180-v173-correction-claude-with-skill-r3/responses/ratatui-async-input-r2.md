These are two separate bugs, but both come from how Crossterm's async input is set up.

## 1. `EventStream` doesn't resolve: the `event-stream` feature is off

Crossterm only provides `EventStream` when its `event-stream` feature is enabled. Ratatui 0.30 re-exports Crossterm but doesn't turn that feature on. Add Crossterm yourself at the same version Ratatui uses (0.29 by default), so Cargo merges the two into one crate:

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }
futures = "0.3"          # for StreamExt::next()
tokio = { version = "1", features = ["full"] }
tokio-util = "0.7"       # CancellationToken
```

Keep importing through the re-export so you always get the version Ratatui was built against:

```rust
use ratatui::crossterm::event::{Event, EventStream};
use futures::StreamExt;
```

Then run `cargo tree -p crossterm` and check that only **one** version appears. If you get two versions that don't merge (e.g. 0.28 and 0.29), each has its own event queue and its own raw-mode tracking. That causes input bugs that are hard to trace.

## 2. Lost keystrokes: your input task is still reading while the editor runs

Your background task is still polling `EventStream` while `$EDITOR` runs, and both read the same TTY. The task takes your first few keystrokes, and the editor's replies to terminal queries, before the editor sees them. Calling `ratatui::restore()` doesn't stop the task.

The fix is to **cancel the reader and wait for it to finish** before handing the terminal over. When the editor exits, set the terminal back up and start a new reader. Make the reader cancellable:

```rust
fn spawn_input(tx: mpsc::UnboundedSender<Event>, stop: CancellationToken) -> JoinHandle<()> {
    tokio::spawn(async move {
        let mut events = EventStream::new();
        loop {
            tokio::select! {
                _ = stop.cancelled() => break,
                next = events.next() => match next {
                    Some(Ok(event)) => { let _ = tx.send(event); }
                    _ => break,
                },
            }
        }
    })
}
```

Then do the handoff in this order (this follows Ratatui's [spawn-vim recipe](https://ratatui.rs/recipes/apps/spawn-vim/)):

```rust
async fn run_editor(terminal: &mut DefaultTerminal, app: &mut App) -> Result<ExitStatus> {
    // 1. Stop the reader and wait until it has actually exited
    app.input_stop.cancel();
    if let Some(h) = app.input_task.take() { h.await?; }

    // 2. Give the shell its terminal back
    ratatui::restore();

    // 3. Run the editor; keep its result instead of `?`-ing it yet
    let editor = std::env::var("EDITOR").unwrap_or_else(|_| "vi".into());
    let child = tokio::task::spawn_blocking({
        let path = app.path.clone();
        move || std::process::Command::new(editor).arg(path).status()
    }).await?;

    // 4. Set the terminal up again and clear it so the next draw repaints everything
    let reentry = enable_raw_mode()
        .and_then(|()| execute!(stdout(), EnterAlternateScreen))
        .and_then(|()| terminal.clear());

    // 5. Start a fresh reader with a new token (a cancelled token can't be reused)
    app.input_stop = CancellationToken::new();
    app.input_task = Some(spawn_input(app.tx.clone(), app.input_stop.clone()));

    // 6. Reload anything the editor may have changed; a redraw only repaints old state
    app.reload();

    match (child, reentry) {
        (Ok(status), Ok(())) => { terminal.draw(|f| app.draw(f))?; Ok(status) }
        (child, reentry) => Err(eyre!("editor: {child:?}; reentry: {reentry:?}")),
    }
}
```

Points that matter:
- **Wait for the task; don't just cancel it.** `cancel()` only sends the signal. Until `h.await` returns, the task can still read one more key.
- **Don't block the Tokio runtime** with a plain `Command::status()`. Use `spawn_blocking` as above, or `tokio::process::Command`.
- **Keep the editor's result and the re-setup result separate.** If you `?` the editor's result straight away, a failure skips steps 4–5 and leaves the user in a broken terminal. If both fail, report both.
- **Reload after the editor exits** (`app.reload()`). Otherwise the screen comes back showing the file as it was before the edit.
- If you add Ctrl+Z suspend later, use the same stop → restore → resume steps. Send SIGTSTP only after the terminal is restored, and offer a different action on Windows, which has no job-control signals.
