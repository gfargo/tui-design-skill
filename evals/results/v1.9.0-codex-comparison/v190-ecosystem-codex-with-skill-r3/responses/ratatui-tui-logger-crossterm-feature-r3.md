No. In **tui-logger 0.18**, the `crossterm` and `termion` features gate its **demo example**, not the log widget.

This is sufficient for your app:

```toml
[dependencies]
ratatui = "0.30"  # crossterm backend enabled by default
tui-logger = "0.18"
```

tui-logger depends on Ratatui with default features disabled; your app selects the backend. The widget renders into Ratatui’s buffer without needing its own crossterm feature.

Handle keyboard input in your app and translate relevant keys into `tui_logger::TuiWidgetEvent` values.

See the [tui-logger 0.18 feature definitions](https://docs.rs/crate/tui-logger/0.18.0/features).