You have two separate problems, and both come from how Crossterm's async input works.

## 1. `EventStream` doesn't resolve: the feature isn't enabled

`EventStream` sits behind Crossterm's `event-stream` feature, and Ratatui doesn't turn that feature on. Add Crossterm directly, at the same version Ratatui 0.30 uses (0.29), so Cargo merges the two into one crate:

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }
futures = "0.3"          # for StreamExt::next()
tokio = { version = "1", features = ["full"] }
tokio-util = "0.7"       # CancellationToken
```

Keep importing through the re-export (`use ratatui::crossterm::event::{Event, EventStream};`). Then run `cargo tree -p crossterm` and make sure only **one** version appears. If two semver-incompatible versions get pulled in, each one keeps its own event queue and its own raw-mode state. That causes very confusing input bugs.

## 2. Lost keystrokes in `$EDITOR`: your reader is still running

The `EventStream` task is still reading stdin while the editor runs. It takes your first few keypresses, and the terminal's replies to the editor's capability queries, before the editor can read them. Restoring the terminal doesn't stop the reader. You have to cancel the reader and wait for it to finish **before** you hand over the terminal, then start a fresh one afterward.

Make the reader cancellable:

```rust
fn spawn_input(tx: mpsc::UnboundedSender<Event>, stop: CancellationToken) -> JoinHandle<()> {
    tokio::spawn(async move {
        let mut events = EventStream::new();
        loop {
            tokio::select! {
                _ = stop.cancelled() => break,
                next = events.next() => match next {
                    Some(Ok(ev)) => { let _ = tx.send(ev); }
                    _ => break,
                },
            }
        }
    })
}
```

Then follow this order for the handoff:

```rust
async fn run_editor(terminal: &mut DefaultTerminal, app: &mut App) -> Result<ExitStatus> {
    // 1. Stop the reader and wait for it to finish.
    app.input_stop.cancel();
    app.input_task.take().unwrap().await?;

    // 2. Give the terminal back to the shell.
    ratatui::restore();

    // 3. Run the editor; keep its result (no `?` yet).
    let editor = std::env::var("EDITOR").unwrap_or_else(|_| "vi".into());
    let child = tokio::process::Command::new(editor).arg(&app.path).status().await;

    // 4. Re-enter raw mode and the alternate screen; clear so the next draw repaints every cell.
    let reentry = enable_raw_mode()
        .and_then(|()| execute!(stdout(), EnterAlternateScreen))
        .and_then(|()| terminal.clear());

    // 5. Start a new reader with a new token (a cancelled token can't be reused).
    app.input_stop = CancellationToken::new();
    app.input_task = Some(spawn_input(app.tx.clone(), app.input_stop.clone()));

    // 6. Reload anything the editor may have changed. A redraw alone only repaints old state.
    app.reload();

    match (child, reentry) {
        (Ok(status), Ok(())) => { terminal.draw(|f| app.draw(f))?; Ok(status) }
        (child, reentry) => Err(eyre!("child: {child:?}; reentry: {reentry:?}")),
    }
}
```

A few details:
- **Order matters.** Cancel and wait for the reader, then restore, then spawn the editor. If you only cancel without waiting, the task can still grab a key during the handoff.
- **Keep both results.** If the editor and the re-entry both fail, report both. Using `?` on the editor result would skip re-entry and leave the terminal half-restored.
- **Use `tokio::process::Command`.** It avoids blocking a runtime worker while the editor runs. The `std` version works, but it holds that thread for the whole editing session.
- **Ctrl+Z works the same way.** If you add suspend support later, use the same sequence. Send SIGTSTP only after restoring, and re-enter and redraw after SIGCONT. This is Unix-only, so give Windows users another path.

This is the same pattern as Ratatui's [spawn-vim recipe](https://ratatui.rs/recipes/apps/spawn-vim/), adapted for an async reader.
