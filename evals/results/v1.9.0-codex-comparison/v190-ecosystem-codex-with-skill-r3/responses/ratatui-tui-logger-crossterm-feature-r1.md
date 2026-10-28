No. In **tui-logger 0.18**, the `crossterm` and `termion` features support its demo example; they aren’t required to compile or render the widget.

Your app selects the Ratatui backend. This is sufficient with Ratatui’s defaults, which include Crossterm:

```toml
[dependencies]
ratatui = "0.30"
tui-logger = "0.18"
```

`tui-logger` depends on Ratatui with default features disabled, so it doesn’t choose a backend for you. Handle keyboard input in your app and translate relevant keys into `TuiWidgetEvent`s.

The blog’s requirement doesn’t apply to this version’s widget.