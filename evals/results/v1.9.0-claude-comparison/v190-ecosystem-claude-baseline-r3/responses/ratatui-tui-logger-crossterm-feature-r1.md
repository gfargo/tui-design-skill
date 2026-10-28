No, that's very likely wrong. I couldn't check it here because there's no tui-logger source in your cargo registry and no project in this directory. So this is based on how the crate is built, not on a compile test.

**Why the backend doesn't matter:** `TuiLoggerWidget` and `TuiLoggerSmartWidget` implement Ratatui's `Widget` trait. They only draw into a `Buffer`. They never use the terminal backend, so they work with crossterm, termion or termwiz without any backend feature on tui-logger.

**What tui-logger's `crossterm`/`termion` features do:** They pass the matching feature through to `ratatui` (like `ratatui/crossterm`). They're mainly there for tui-logger's own demo and examples. Your app already turns on crossterm support in Ratatui, either through Ratatui's default features or your own `features = ["crossterm"]`. Cargo combines features across the dependency graph, so enabling it again through tui-logger changes nothing.

The blog post may be describing very old versions. The tui-rs-era tui-logger did make you choose a backend with features like `tui-crossterm`.

**What actually breaks compilation:** two Ratatui versions in your dependency tree. If tui-logger pulls in a different Ratatui than your app, you get errors like "expected `ratatui::buffer::Buffer`, found a different `Buffer`". To check:

```sh
cargo add tui-logger@0.18          # prints the crate's available features
cargo tree -i ratatui              # should show exactly one ratatui (0.30.x)
```

If `cargo tree` shows one Ratatui 0.30 and the build passes, you're done. Only add `features = ["crossterm"]` if a real compile error points to it, and so far nothing suggests one would.
