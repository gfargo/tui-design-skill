You have two separate problems.

## 1. `EventStream` doesn't resolve: the feature is off

`EventStream` sits behind Crossterm's `event-stream` feature, and Ratatui doesn't turn that feature on. You need to add Crossterm yourself, using **the same version Ratatui 0.30 uses** so Cargo merges them into one crate:

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }
tokio = { version = "1", features = ["full"] }
tokio-util = "0.7"      # CancellationToken
futures = "0.3"         # StreamExt for events.next()
```

Keep importing through `ratatui::crossterm::event::{Event, EventStream}`. If your `crossterm` version doesn't match Ratatui's, you get two copies of Crossterm. The feature then lands on the wrong copy, and Ratatui's event types stop matching yours.

## 2. Lost keystrokes: your input reader is still running

Your `EventStream` task keeps reading stdin while `$EDITOR` runs. It takes the first keys you type, and the terminal's replies to the editor's capability queries, before the editor sees them. Once the reader has stopped they go to the editor. The fix is to **cancel the reader and wait for it to finish before you give the terminal to the editor**, then start a new reader afterwards.

Make the reader cancellable:

```rust
use futures::StreamExt;
use ratatui::crossterm::event::{Event, EventStream};
use tokio::{sync::mpsc, task::JoinHandle};
use tokio_util::sync::CancellationToken;

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

Then do the handoff in this order (this follows Ratatui's spawn-vim recipe):

```rust
// 1. Stop input. Wait for the task to finish; cancelling alone isn't enough.
stop.cancel();
input.await?;

// 2. Give the terminal back to the shell.
ratatui::restore();

// 3. Run the editor. Keep its result; don't `?` it yet.
let editor = std::env::var("EDITOR").unwrap_or_else(|_| "vi".into());
let child = std::process::Command::new(editor).arg(&path).status();

// 4. Re-enter raw mode and the alternate screen, then clear so the next draw repaints every cell.
let reentry = enable_raw_mode()
    .and_then(|()| execute!(stdout(), EnterAlternateScreen))
    .and_then(|()| terminal.clear());

// 5. Start a NEW reader with a NEW token. A cancelled token can't be reused.
let stop = CancellationToken::new();
let input = spawn_input(tx.clone(), stop.clone());

// 6. Reload anything the editor may have changed, then redraw.
app.reload();
```

A few details:
- **Report both errors.** If the editor fails and re-entry also fails, include both in the error. Using `?` on either one alone hides the other.
- **Run the editor with blocking `std::process::Command::status()`.** That's correct here because the UI is meant to be paused. If you'd rather not block a Tokio worker thread, wrap the call in `spawn_blocking` or use `tokio::process`.
- **Reload, don't just redraw.** A redraw only repaints the data you already had in memory. If the editor changed a file, re-read it before drawing.
- **Use the same order on exit.** Cancel and await the reader before the final `ratatui::restore()`, or it can take input after your app has quit.

Reference: the skill's `references/ecosystem-rust.md`, sections *Async with Tokio* and *Lifecycle and terminal handoff*.
