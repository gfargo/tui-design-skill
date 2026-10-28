No. **tui-logger’s `crossterm` feature is for its demo, not required by its widgets.** Its manifest explicitly says the backend features are “only necessary for the demo.”

Enable the backend on your app’s Ratatui dependency:

```toml
[dependencies]
ratatui = { version = "0.30", features = ["crossterm"] }
tui-logger = "0.18"
```

tui-logger 0.18 uses Ratatui 0.30 with default features disabled. Its widgets render into Ratatui buffers without depending on a terminal backend. Enabling `tui-logger/crossterm` merely forwards to `ratatui/crossterm` and enables a demo feature guard.

Source: [tui-logger’s Cargo.toml](https://github.com/gin66/tui-logger/blob/master/Cargo.toml).