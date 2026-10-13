These are two separate issues: a Cargo feature gate and competing readers of terminal input.

`EventStream` requires Crossterm’s **`event-stream` feature**; enabling Tokio doesn’t enable it. For Ratatui 0.30’s Crossterm backend, use the matching Crossterm version:

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }
futures-util = "0.3"
```

Then import:

```rust
use crossterm::event::EventStream;
use futures_util::StreamExt;
```

Cargo combines features only for the **same package version**. If you enabled `event-stream` on a different Crossterm version from the one you import or re-export, it won’t help. Check with `cargo tree -e features` and `cargo tree -d`.

The disappearing keystrokes usually mean **your app’s input reader is still running while `$EDITOR` owns the terminal**. Restoring cooked mode and leaving the alternate screen changes terminal behavior; it doesn’t stop a Tokio task or background thread from consuming stdin.

Make editor launch a coordinated handoff:

1. Stop the app’s input reader and wait for it to stop. A pause flag alone is insufficient if it’s already blocked reading.
2. Disable raw mode, leave the alternate screen, and restore any enabled mouse/focus/paste modes.
3. Launch the editor with inherited stdin/stdout/stderr and await its exit.
4. Restore the TUI modes, restart input handling, and redraw.

`tokio::spawn` cancellation also needs care: dropping a `JoinHandle` leaves the task running, and aborting a `spawn_blocking` task doesn’t stop an already-running blocking reader. For reliable handoffs, a dedicated input thread with bounded `poll` timeouts and a stop acknowledgement is often easiest.

Also, Crossterm forbids mixing `EventStream` with its synchronous `event::read`/`poll` APIs. Give terminal input one owner at a time.