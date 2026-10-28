No. In **tui-logger 0.18**, the `crossterm` and `termion` features gate its demo example, **not the logger widget**.

The widget is backend-independent. tui-logger depends on Ratatui with default features disabled; your app chooses the backend.

This is sufficient for your setup:

```toml
[dependencies]
ratatui = "0.30" # enables Crossterm by default
tui-logger = "0.18"
```

Handle keyboard input in your app and translate relevant keys into tui-logger’s `TuiWidgetEvent`s.

The tui-design skill’s Rust reference explicitly documents this distinction. I couldn’t independently retrieve the upstream docs in this session.