You likely have two separate problems: a missing Cargo feature and an input reader still running during editor handoff.

**`EventStream` is feature-gated.** Ratatui does not enable Crossterm’s `event-stream` feature. For Ratatui 0.30’s default Crossterm 0.29 backend:

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }
futures = "0.3"
```

Keep imports aligned with Ratatui’s backend:

```rust
use futures::StreamExt;
use ratatui::crossterm::event::{Event, EventStream};
```

The direct dependency enables the feature through Cargo feature unification. Check `cargo tree -d` for multiple Crossterm versions: 0.28 and 0.29 have separate event queues and raw-mode tracking. If you deliberately select Ratatui’s `crossterm_0_28` backend, match that version instead. When both backend flags are enabled, 0.29 takes precedence.

**The disappearing editor keystrokes usually mean your TUI reader still owns terminal input.** `ratatui::restore()` changes terminal modes; it does not stop your Tokio task. That reader can consume both the editor’s keys and terminal capability responses.

Use this handoff order:

1. Cancel the input task **and await its termination**, so its `EventStream` is dropped.
2. Restore the terminal, including any mouse/paste modes you enabled.
3. Launch the editor with inherited stdin/stdout/stderr and wait for it.
4. Re-enable raw mode and the alternate screen; call `terminal.clear()`.
5. Reload the edited data, start a fresh input reader with a **new cancellation token**, and redraw.

The critical synchronization is:

```rust
stop.cancel();
input.await?;          // reader has stopped before the editor starts
ratatui::restore();
```

Keep the child’s result until terminal reentry has been attempted—even a failed editor launch must restore the TUI. With Tokio, use `tokio::process::Command` or move blocking subprocess waiting off the runtime thread. Also avoid mixing `EventStream` with another `event::read()`/`poll()` reader.

A full redraw restores the display; reloading the file restores the app’s data. Both are needed after editing.