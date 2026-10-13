You likely have two separate problems: a missing Cargo feature and an input reader that remains active while `$EDITOR` owns the terminal.

**`EventStream` requires Crossterm’s `event-stream` feature.** Ratatui’s Crossterm backend doesn’t enable it automatically. For the default Crossterm version used by Ratatui 0.30:

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }
futures-util = "0.3"
```

```rust
use crossterm::event::EventStream;
use futures_util::StreamExt;
```

Cargo features unify **for the same package version**. If you enabled `event-stream` on another Crossterm version, that won’t enable it on Ratatui’s re-export. Check with:

```sh
cargo tree -i crossterm
cargo tree -e features
```

**The disappearing keystrokes usually mean your app and the editor are both reading stdin.** Leaving raw mode and the alternate screen restores terminal settings; it doesn’t stop your Tokio input task. Suspending rendering also doesn’t stop it.

Hand the terminal over in this order:

1. Signal the input task to stop, let it drop its `EventStream`, and **await its completion**.
2. Disable raw mode, leave the alternate screen, and undo any mouse capture or other terminal modes you enabled.
3. Launch the editor and wait for it to exit.
4. Restore the TUI’s terminal modes, clear/redraw, and create a fresh input stream/task.

Watch for these traps:

- `JoinHandle::abort()` requests cancellation; await the handle before launching the editor.
- Aborting an already-running `spawn_blocking` task does **not** stop its blocking input loop. That loop needs cooperative shutdown, typically using bounded `poll` timeouts.
- Don’t mix `EventStream` with another Crossterm `read`/`poll` reader.

The key requirement is exclusive ownership of terminal input: the app’s reader must be fully stopped before the editor starts.