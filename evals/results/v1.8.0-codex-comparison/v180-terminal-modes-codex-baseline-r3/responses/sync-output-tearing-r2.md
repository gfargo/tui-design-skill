Yes—**synchronized output**, also called synchronized updates (**DEC private mode 2026**). Kitty and WezTerm support it. The terminal continues processing output but holds the displayed image until your frame is complete, reducing visible tearing.

The escape sequences are:

```text
ESC [ ? 2026 h    begin synchronized update
ESC [ ? 2026 l    end synchronized update
```

With Ratatui’s Crossterm backend, bracket each `Terminal::draw`:

```rust
use std::io::{self, stdout};
use crossterm::{
    execute,
    terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate},
};

fn draw_frame(
    terminal: &mut ratatui::DefaultTerminal,
) -> io::Result<()> {
    let mut output = stdout();

    execute!(output, BeginSynchronizedUpdate)?;

    let draw_result = terminal.draw(|frame| {
        // Render your table and other widgets here.
    });

    // Attempt this even when draw() returned an error.
    let end_result = execute!(output, EndSynchronizedUpdate);

    draw_result?;
    end_result?;
    Ok(())
}
```

`DefaultTerminal` assumes a recent Ratatui version using its default Crossterm backend; adapt the type for your version.

For safe use:

- **Prepare data before beginning.** Keep only the actual draw inside the synchronized region. Never wait for input, sleep, or do network work there.
- **Always send the end sequence.** The example handles ordinary drawing errors. For panic safety, add an RAII guard whose `Drop` makes a best-effort attempt to send and flush `EndSynchronizedUpdate`, and include it in terminal restoration. Destructors cannot help with an abort or forced process termination.
- **Keep output ordered.** Send begin, frame output, and end to the same terminal stream, flushing the end sequence. Prevent concurrent logging or other writers from interleaving with rendering.
- **Avoid nested regions.** The mode is not a reference-counted lock; an inner end can release the outer update.
- **Check the full terminal path.** A multiplexer such as tmux can affect support. Query with `CSI ? 2026 $ p` (DECRQM) if you need detection, using a bounded timeout and an input parser that preserves unrelated keyboard events. Don’t infer support solely from `$TERM`.

Unsupported terminals generally ignore these sequences, so rendering still works without the visual improvement. Terminal watchdog timeouts are a recovery mechanism, not a substitute for ending each frame.

Ratatui already diffs its buffers. Synchronized output makes those writes appear together; it won’t reduce table computation or drawing cost.