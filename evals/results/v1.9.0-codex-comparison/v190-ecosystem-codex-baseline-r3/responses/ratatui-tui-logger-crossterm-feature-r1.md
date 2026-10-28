No. **tui-logger 0.18’s widgets are backend-independent**; they don’t need a `crossterm` feature to render in your Ratatui 0.30 app. The blog’s advice refers to older dependency arrangements.

Configure the backend on Ratatui:

```toml
[dependencies]
ratatui = { version = "0.30", features = ["crossterm"] }
tui-logger = "0.18"
```

Ratatui also enables `crossterm` by default, so explicitly listing it is optional unless you disable default features.

If you get incompatible `Widget`, `Buffer`, or `Rect` errors, check for conflicting dependency versions with `cargo tree -d`; enabling a backend feature won’t resolve those.

I couldn’t retrieve the published source in this session to independently verify the release metadata.