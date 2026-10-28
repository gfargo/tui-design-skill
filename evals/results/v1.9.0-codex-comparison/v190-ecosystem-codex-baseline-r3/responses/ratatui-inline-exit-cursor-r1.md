Use an **inline viewport** with a fixed height. `ratatui::run(...)` uses the default full-screen setup; for inline rendering, use `run_with_options`:

```rust
use ratatui::{TerminalOptions, Viewport};

fn main() -> std::io::Result<()> {
    ratatui::run_with_options(
        TerminalOptions {
            viewport: Viewport::Inline(10),
        },
        |terminal| {
            // Run your event/render loop here.
            // terminal.draw(|frame| { ... })?;
            Ok(())
        },
    )
}
```

When building the terminal yourself, set the same viewport:

```rust
let mut terminal = ratatui::init_with_options(TerminalOptions {
    viewport: Viewport::Inline(10),
});

// Run the UI, preserving its result so cleanup always happens.
let result = run_app(&mut terminal);

ratatui::restore();

// Move below the inline UI before returning control to the shell.
println!();

result
```

The newline prevents the next shell prompt from sharing the UI’s final line. Restore the terminal **before** printing it, so raw mode is disabled.

If your installed Ratatui version lacks `run_with_options`, use the second pattern.