There's no project in the working directory, so this answer is based on how these crates behave, not on your code. These are two separate problems, and the second one comes from how `EventStream` works.

## 1. `EventStream` doesn't resolve

`crossterm::event::EventStream` only exists when crossterm's **`event-stream`** feature is on. Ratatui doesn't turn it on, so the type isn't there.

Add crossterm yourself at the **same version ratatui 0.30 uses (0.29)** and enable the feature. You also need `futures` for `StreamExt::next()`:

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }
futures = "0.3"
tokio = { version = "1", features = ["full"] }
```

Getting the version right matters. If you pull in a different crossterm (e.g. 0.28), you end up with two copies. Their `Event`/`KeyEvent` types won't match ratatui's, and each copy has its own global input reader. Because Cargo merges features across the dependency tree, `ratatui::crossterm::event::EventStream` will work too once the feature is on. Importing through the `ratatui::crossterm` re-export is a good way to stay on one version.

## 2. Keystrokes vanish after opening `$EDITOR`

Your app is still reading stdin while the editor runs. Polling `EventStream` starts a crossterm reader that waits on stdin in the background. If the stream or the task that owns it is still alive when you start the editor, the two processes compete for the same input. Your app wins the first few bytes, and the editor never sees them. A thread looping on `event::read()` causes the same problem.

The fix is to **fully stop the input reader before starting the editor**, then restart it afterwards. Pausing a flag doesn't work, because a read is already waiting. You have to drop the `EventStream`, which wakes and shuts down its reader, and wait for the task that owns it to finish.

```rust
use futures::StreamExt;
use ratatui::crossterm::{
    event::{Event, EventStream},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use tokio::{sync::mpsc, task::JoinHandle};
use tokio_util::sync::CancellationToken;

fn spawn_input(tx: mpsc::UnboundedSender<Event>) -> (CancellationToken, JoinHandle<()>) {
    let token = CancellationToken::new();
    let t = token.clone();
    let handle = tokio::spawn(async move {
        let mut events = EventStream::new();
        loop {
            tokio::select! {
                _ = t.cancelled() => break,
                Some(Ok(ev)) = events.next() => { let _ = tx.send(ev); }
            }
        }
        // `events` is dropped here, which shuts down crossterm's reader
    });
    (token, handle)
}

async fn open_editor(
    terminal: &mut ratatui::DefaultTerminal,
    input: &mut (CancellationToken, JoinHandle<()>),
    tx: &mpsc::UnboundedSender<Event>,
    path: &std::path::Path,
) -> std::io::Result<()> {
    // 1. Stop reading stdin, and wait until the reader is really gone
    input.0.cancel();
    let _ = (&mut input.1).await;

    // 2. Give the terminal back
    execute!(std::io::stdout(), LeaveAlternateScreen)?;
    disable_raw_mode()?;

    // 3. Run the editor (tokio::process so the runtime isn't blocked)
    let editor = std::env::var("EDITOR").unwrap_or_else(|_| "vi".into());
    tokio::process::Command::new(editor).arg(path).status().await?;

    // 4. Take the terminal back and restart input
    enable_raw_mode()?;
    execute!(std::io::stdout(), EnterAlternateScreen)?;
    terminal.clear()?; // force a full redraw
    *input = spawn_input(tx.clone());
    Ok(())
}
```

This sketch uses `tokio-util` for `CancellationToken`. A `oneshot` channel or `JoinHandle::abort()` followed by awaiting the handle works the same way.

The important parts:
- **Cancel the task, then await it.** Calling `cancel()` without awaiting leaves a short window where the reader is still alive.
- **Undo whatever you set up.** If you enabled mouse capture, bracketed paste, or keyboard enhancement flags, turn them off before starting the editor and back on afterwards. Otherwise the editor receives escape-sequence garbage.
- **Call `terminal.clear()` afterwards.** Ratatui's buffer diffing doesn't know the editor drew over the screen, so without this you get a partly stale display.
