There's no Rust project in this directory, so this answer isn't based on your code. Both symptoms usually come from the same place: how crossterm is wired into a Ratatui 0.30 app.

## 1. `EventStream` doesn't resolve

`crossterm::event::EventStream` only exists when crossterm's **`event-stream`** feature is enabled, and Ratatui doesn't turn that feature on. Enable it on your own crossterm dependency, and **use the same crossterm version Ratatui uses**. If the versions differ, Cargo builds two separate crossterm crates. The feature then lands on the wrong one, and you'll also see type mismatches between `ratatui::crossterm::event::Event` and `crossterm::event::Event`.

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }  # must match ratatui's crossterm
futures = "0.3"   # for StreamExt::next()
tokio = { version = "1", features = ["full"] }
```

Check with `cargo tree -i crossterm`. You want exactly one version in the output. Because Cargo unifies features within a single version, you can then import from either `crossterm::…` or `ratatui::crossterm::…` and get the same types.

## 2. The first keystrokes in `$EDITOR` vanish

`EventStream` starts a background reader that keeps polling stdin. If it's still alive when you launch the editor, it reads the first bytes you type (into crossterm's internal buffer, or your app's event channel) before the editor gets them. Leaving raw mode or the alternate screen doesn't stop it. You have to **stop and drop the stream** before handing over the terminal, and create a new one afterwards.

The usual pattern, with the event reader in its own task:

```rust
use crossterm::{
    event::EventStream,
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use futures::StreamExt;
use tokio_util::sync::CancellationToken;

fn spawn_events(tx: tokio::sync::mpsc::UnboundedSender<Event>, cancel: CancellationToken)
    -> tokio::task::JoinHandle<()>
{
    tokio::spawn(async move {
        let mut events = EventStream::new();
        loop {
            tokio::select! {
                _ = cancel.cancelled() => break,          // drops `events` → reader stops
                Some(Ok(ev)) = events.next() => { let _ = tx.send(ev); }
            }
        }
    })
}

async fn open_editor(app: &mut App, terminal: &mut DefaultTerminal, path: &Path) -> io::Result<()> {
    // 1. Stop the event reader and WAIT for it to finish
    app.event_cancel.cancel();
    if let Some(h) = app.event_task.take() { let _ = h.await; }

    // 2. Hand the terminal back
    execute!(io::stdout(), LeaveAlternateScreen)?;
    disable_raw_mode()?;

    let editor = std::env::var("EDITOR").unwrap_or_else(|_| "vi".into());
    let status = tokio::process::Command::new(editor).arg(path).status().await;

    // 3. Take it back, force a full redraw, restart the reader
    enable_raw_mode()?;
    execute!(io::stdout(), EnterAlternateScreen)?;
    terminal.clear()?;

    app.event_cancel = CancellationToken::new();
    app.event_task = Some(spawn_events(app.event_tx.clone(), app.event_cancel.clone()));
    status.map(|_| ())
}
```

Things to get right:

- **Await the task handle.** Calling `cancel()` alone just sends a signal. The old reader can still grab a key before it notices.
- **Make sure nothing else is polling.** No `crossterm::event::poll`/`read` in a tick loop, and no second `EventStream` somewhere else. Any of them will also take input from the editor.
- **Call `terminal.clear()` after returning.** Ratatui's buffer diff assumes the screen still shows its last frame, so without a clear you get leftover artifacts from the editor.
- If you enabled mouse capture, bracketed paste, or keyboard enhancement flags, disable them before launching the editor and re-enable them afterwards. Otherwise the editor receives escape sequences it doesn't expect.

If you paste your `Cargo.toml` and the event loop and editor-launch code, I can point to the exact line causing it.
