Two separate issues: a disabled Cargo feature and an input reader that likely keeps running during the editor handoff.

**`EventStream` requires Crossterm’s `event-stream` feature.** Ratatui doesn’t enable it. With Ratatui 0.30’s default Crossterm 0.29 backend:

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }
```

Keep imports tied to Ratatui’s selected version:

```rust
use ratatui::crossterm::event::{Event, EventStream};
use futures::StreamExt;
```

The matching direct dependency enables the feature through Cargo feature unification. Check `cargo tree -d` for multiple Crossterm versions; if you explicitly selected `crossterm_0_28`, match that version instead.

**The vanished keystrokes usually mean your TUI reader is competing with `$EDITOR` for terminal input.** Restoring terminal modes alone doesn’t stop an `EventStream` task. The handoff must follow this order:

1. Cancel the input task **and await its completion**, so its `EventStream` is dropped.
2. Call `ratatui::restore()` and restore any additional modes your app enabled.
3. Launch the editor with inherited stdin/stdout/stderr and wait for it. In Tokio, use `tokio::process::Command::status().await`.
4. Re-enable raw mode and the alternate screen; clear the Ratatui terminal.
5. Reload the edited data, start a fresh input reader with a **new cancellation token**, and redraw.

The critical synchronization is:

```rust
stop.cancel();
input.await?; // reader has finished before the editor gets terminal ownership
ratatui::restore();
```

Cancellation without awaiting leaves a race. Also avoid mixing `EventStream` with another `event::read()`/`poll()` reader.

Preserve the editor’s result and attempt terminal reentry even if spawning or waiting fails—an early `?` can otherwise leave the app unable to resume.