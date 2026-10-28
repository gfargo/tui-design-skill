No. **tui-logger’s `crossterm` feature is for its demo, not required by the widget.** Its manifest explicitly says so; the feature forwards `ratatui/crossterm` and enables the demo’s backend-selection marker. Your app selects its backend through Ratatui. [Source](https://docs.rs/crate/tui-logger/0.18.3/source/Cargo.toml.orig)

For Ratatui 0.30, use:

```toml
[dependencies]
ratatui = { version = "0.30", features = ["crossterm"] }
tui-logger = "0.18.3"
```

Ratatui enables Crossterm by default, so the explicit feature above is optional.

The patch version matters: **tui-logger 0.18.3 updated to Ratatui 0.30**. If your lockfile retains an earlier 0.18 release, update it; enabling a backend feature won’t fix incompatible Ratatui widget types. [Changelog](https://docs.rs/crate/tui-logger/0.18.3/source/CHANGELOG.md)