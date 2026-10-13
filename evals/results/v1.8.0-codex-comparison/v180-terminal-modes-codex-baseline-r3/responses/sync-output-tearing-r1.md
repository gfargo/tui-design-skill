Yes—**synchronized output**, also called synchronized updates (**DEC private mode 2026**). Kitty and WezTerm support it. It lets the terminal process a frame’s output while holding the previous image onscreen, then display the completed update, reducing visible tearing.

The protocol is:

```text
ESC [ ? 2026 h    begin synchronized update
…frame output…
ESC [ ? 2026 l    end synchronized update
```

With Ratatui’s Crossterm backend, wrap each draw using Crossterm’s `BeginSynchronizedUpdate` and `EndSynchronizedUpdate`. For a terminal writing to stdout:

```rust
use std::io::{self, Stdout};
use crossterm::{
    execute,
    terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate},
};
use ratatui::{backend::CrosstermBackend, Frame, Terminal};

fn draw_frame(
    terminal: &mut Terminal<CrosstermBackend<Stdout>>,
    render: impl FnOnce(&mut Frame),
) -> io::Result<()> {
    execute!(io::stdout(), BeginSynchronizedUpdate)?;

    let draw_result = terminal.draw(render).map(|_| ());

    // Attempt and flush the end marker even if drawing returned an error.
    let end_result = execute!(io::stdout(), EndSynchronizedUpdate);

    draw_result.and(end_result)
}
```

For safe use:

- **Bracket one frame only.** End the update before sleeping, waiting for input, or doing slow work. Precompute expensive table data before beginning.
- **Handle errors and panics.** The example handles returned errors; add a best-effort drop guard for panic unwinding, and send the end marker in your terminal cleanup/panic hook. Don’t rely on an emulator timeout.
- **Use the same output stream as your backend**, and keep concurrent logging away from it.
- **Avoid nested brackets.** Check whether your Ratatui version or existing wrapper already synchronizes draws; this mode is not a nesting counter.
- **Allow unsupported terminals to fall back.** They generally ignore these mode commands. For capability detection, query `CSI ? 2026 $ p` and parse the DECRQM response through your existing input reader with a bounded timeout. Test through tmux/SSH too.

This addresses presentation tearing; it doesn’t reduce rendering cost. Ratatui already diffs its buffers, so also avoid clearing the terminal or forcing a full repaint every tick.

References: [synchronized-output specification](https://github.com/contour-terminal/terminal-synchronized-output), [Crossterm commands](https://docs.rs/crossterm/latest/crossterm/terminal/struct.BeginSynchronizedUpdate.html).