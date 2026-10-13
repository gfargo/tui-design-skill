I didn't find a project in the working directory, so this is based on how Ratatui, crossterm and Tokio usually fit together. These are two separate problems.

## 1. `EventStream` doesn't resolve

`crossterm::event::EventStream` only exists when crossterm's **`event-stream`** feature is on. Ratatui doesn't turn that feature on for you. A second common problem is ending up with two crossterm versions: one that Ratatui uses and one you added yourself. Their `Event` types won't match.

Fix: depend on crossterm directly, at the **same version Ratatui 0.30 uses (0.29)**, and enable the feature:

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }
futures = "0.3"   # for StreamExt::next()
tokio = { version = "1", features = ["full"] }
```

Because the version matches, Cargo merges the features into one crossterm. `ratatui::crossterm` and `crossterm` then refer to the same crate. Run `cargo tree -d -i crossterm` to check. If it lists two versions, that's your mismatch.

```rust
use crossterm::event::{EventStream, Event};
use futures::StreamExt;

let mut events = EventStream::new();
while let Some(Ok(ev)) = events.next().await { /* ... */ }
```

## 2. Keystrokes disappear when you open `$EDITOR`

Your app is still reading stdin while the editor runs. If an `EventStream` is still alive, or a task is still sitting in `events.next().await` (often inside a `tokio::select!` loop or a spawned input task), crossterm keeps reading from the TTY. Your app and the editor end up competing for the same bytes, and your app wins the first few.

Fix: **stop reading input completely before you spawn the editor, then start again afterwards.**

1. Cancel the input task, or drop the `EventStream`. Dropping it wakes and stops crossterm's background reader.
2. Restore the terminal: leave the alternate screen and disable raw mode.
3. Run the editor and **wait for it to exit**. Use a blocking call such as `std::process::Command::status()`, or `tokio::process::Command` and `.await` it.
4. Re-enter raw mode and the alternate screen, call `terminal.clear()`, and create a **new** `EventStream`.

```rust
use crossterm::{execute, terminal::{self, EnterAlternateScreen, LeaveAlternateScreen}};
use std::io::stdout;

fn open_editor(
    terminal: &mut ratatui::DefaultTerminal,
    events: &mut Option<EventStream>,
    path: &std::path::Path,
) -> std::io::Result<()> {
    // 1. Stop reading stdin
    events.take(); // drops the EventStream

    // 2. Hand the terminal back
    execute!(stdout(), LeaveAlternateScreen)?;
    terminal::disable_raw_mode()?;

    // 3. Run the editor in the foreground
    let editor = std::env::var("EDITOR").unwrap_or_else(|_| "vi".into());
    let status = std::process::Command::new(editor).arg(path).status();

    // 4. Take the terminal back and resume input
    terminal::enable_raw_mode()?;
    execute!(stdout(), EnterAlternateScreen)?;
    terminal.clear()?;
    *events = Some(EventStream::new());

    status.map(|_| ())
}
```

If input runs in its own spawned task that sends events over a channel, the same idea applies. Before launching the editor, signal that task to stop (for example with a `CancellationToken` or by sending on a oneshot channel) and **await its `JoinHandle`**. Only spawn the editor once the task has actually finished. Calling `abort()` without awaiting can leave the task reading for a moment, and you'll lose input again.

Two smaller things to check:
- Don't wrap the editor in `tokio::task::spawn_blocking` while the `EventStream` is still alive. That has the same competing-reader problem.
- If you enabled mouse capture, bracketed paste or keyboard enhancement flags, turn them off before launching the editor and back on afterwards. Otherwise the editor receives escape sequences it can't handle.
