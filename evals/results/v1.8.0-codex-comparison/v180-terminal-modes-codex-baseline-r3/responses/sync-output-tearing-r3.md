Yes—use **synchronized output**, also called **DEC private mode 2026**. Kitty and WezTerm support it. The terminal continues processing output but holds screen presentation until you finish the update, preventing users from seeing a half-drawn table.

The sequences are:

```text
ESC [ ? 2026 h   begin synchronized update
ESC [ ? 2026 l   end synchronized update
```

With Ratatui’s Crossterm backend, use Crossterm’s `BeginSynchronizedUpdate` and `EndSynchronizedUpdate`. Wrap the **entire `Terminal::draw`**, including its flush:

```rust
use std::io::{self, Stdout};
use crossterm::{
    ExecutableCommand,
    terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate},
};
use ratatui::{backend::CrosstermBackend, Terminal};

fn draw_frame(
    terminal: &mut Terminal<CrosstermBackend<Stdout>>,
) -> io::Result<()> {
    let mut out = io::stdout();
    out.execute(BeginSynchronizedUpdate)?;

    let draw_result = terminal.draw(|frame| {
        // Render your table and other widgets here.
    });

    // Attempt to end the update even if drawing failed.
    let end_result = out.execute(EndSynchronizedUpdate);

    draw_result?;
    end_result?;
    Ok(())
}
```

`execute` flushes the boundary commands. This example assumes both handles write to the same stdout; with a custom writer, send the boundaries through that same output path.

For safe use:

- **Keep the interval short.** Compute data before beginning; end immediately after drawing. Never hold it open while sleeping, awaiting I/O, or waiting for input.
- **Handle every exit path.** The example handles returned errors. Add an RAII guard for panic unwinding, and have terminal cleanup attempt `EndSynchronizedUpdate` before restoring terminal state. Don’t rely on emulator timeouts.
- **Serialize terminal output.** Concurrent logs or another renderer can interleave with the frame. Avoid nested synchronized updates; this is a mode bit, not a nesting counter.
- **Allow a fallback.** Unsupported terminals generally ignore these commands. For explicit detection, query `CSI ? 2026 $ p` using DECRQM and parse its response through your input handling. Support can differ through tmux or SSH; don’t infer it solely from `$TERM`.

This fixes **partial-frame presentation**, not rendering cost. Ratatui already diffs its buffers; avoiding unnecessary ticks and expensive table rebuilding still helps.