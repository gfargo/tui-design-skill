You have two separate issues: a missing Cargo feature and an input reader that likely keeps running during editor handoff.

**`EventStream` is feature-gated.** Ratatui 0.30 defaults to Crossterm 0.29 but doesn’t enable its `event-stream` feature. Add a matching direct dependency to enable it through Cargo feature unification:

```toml
[dependencies]
ratatui = "0.30"
crossterm = { version = "0.29", features = ["event-stream"] }
futures = "0.3"
```

Keep your imports aligned with Ratatui’s backend:

```rust
use futures::StreamExt;
use ratatui::crossterm::event::{Event, EventStream};
```

Check `cargo tree -d` for duplicate Crossterm versions. If you explicitly selected Ratatui’s `crossterm_0_28` backend, enable `event-stream` on **0.28** instead.

**The disappearing keystrokes usually mean your TUI reader is competing with the editor for terminal input.** Calling `ratatui::restore()` changes terminal modes; it doesn’t stop your Tokio input task.

Use this handoff order:

1. Cancel the input task **and await its completion**, ensuring its `EventStream` is dropped.
2. Restore the terminal and any custom mouse, paste, or keyboard modes.
3. Launch the editor with inherited stdin/stdout/stderr and wait for it. Use `tokio::process::Command` for an async wait.
4. Re-enable raw mode and the alternate screen; restore your app’s input modes.
5. Clear the terminal, reload the edited data, and redraw.
6. Spawn a fresh input reader with a **new** cancellation token.

The crucial boundary is:

```rust
stop.cancel();
input.await?;       // reader has exited before the editor starts
ratatui::restore();
// launch and await editor here
```

Also attempt terminal reentry if launching or waiting for the editor fails—an early `?` on the child result can skip recovery. Don’t mix `EventStream` with another Crossterm `read()`/`poll()` input loop.

These recommendations follow the requested [tui-design Rust reference](/Users/gfargo/dev/gfargo/tui-design-skill/.claude/worktrees/amazing-meitner-d3ddd1/plugins/tui-design/skills/tui-design/references/ecosystem-rust.md).