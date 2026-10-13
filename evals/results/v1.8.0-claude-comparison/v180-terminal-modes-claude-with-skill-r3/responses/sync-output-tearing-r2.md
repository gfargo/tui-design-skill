Yes. The feature is **synchronized output, DEC private mode 2026**. You send `CSI ? 2026 h` before a frame and `CSI ? 2026 l` after it, and the terminal shows the whole frame at once instead of painting it as the bytes arrive. kitty and WezTerm both support it, as do foot, Alacritty, Ghostty, iTerm2, Windows Terminal 1.23.20211+ and tmux 3.7+.

Ratatui and crossterm don't turn it on for you. Your app has to send it, using crossterm's `BeginSynchronizedUpdate` and `EndSynchronizedUpdate` commands.

## The one rule: always send the end sequence

If a frame starts and never ends, the terminal stops updating until its own timeout runs out: about 2 s in kitty, 1 s in Ghostty and 150 ms in Alacritty. So the end sequence has to go out on every path: normal draws, draws that return an error, and panics.

```rust
use std::io::{self, Write};
use ratatui::{DefaultTerminal, Frame};
use ratatui::crossterm::{execute, queue, terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate}};

/// Draw one frame inside a synchronized update. The end sequence is sent even if `draw` fails.
fn draw_synced(terminal: &mut DefaultTerminal, render: impl FnOnce(&mut Frame)) -> io::Result<()> {
    queue!(terminal.backend_mut(), BeginSynchronizedUpdate)?;
    let drawn = terminal.draw(render).map(drop);
    let ended = execute!(terminal.backend_mut(), EndSynchronizedUpdate);
    drawn.and(ended)
}
```

**Panics:** if your render code panics (an out-of-bounds index in a cell formatter, say), the begin sequence is already in the buffer and the end sequence never gets sent. `ratatui::restore()` only undoes raw mode and the alternate screen, so it won't clear mode 2026. Add your own handler on top of Ratatui's panic hook. Install it after `ratatui::init()` so it runs first:

```rust
let mut terminal = ratatui::init();
let ratatui_hook = std::panic::take_hook();
std::panic::set_hook(Box::new(move |info| {
    let _ = execute!(io::stdout(), EndSynchronizedUpdate);
    ratatui_hook(info); // Ratatui's restore + the original panic report
}));
```

This only adds the end sequence and then hands off to Ratatui's hook. Don't add a second restore wrapper. Because it runs from the hook, it also works with `panic = "abort"`, where unwinding and `Drop` guards never run.

**Detection is optional.** A terminal that doesn't know mode 2026 ignores it, so sending it every time is the common, low-risk choice. If you need to know for sure (for example, to log whether the fallback is in use), query with DECRQM (`CSI ? 2026 $ p`). Wait for the reply with a timeout and render normally until it arrives, because the reply may come late or never, especially over SSH. Inside tmux older than 3.7 the mode is not supported, so you get no benefit there.

## Also fix why so much changes on each tick

Ratatui compares each frame with the previous one and only sends cells that changed. If you see tearing, a lot of cells are changing on every tick. Mode 2026 hides the symptom, but these fix the cause and also help in terminals that lack mode 2026:

- **Don't call `terminal.clear()` on each tick.** It forces every cell to be repainted. Use it only after resizing the terminal or handing it to another program.
- **Only redraw when something changed.** Skip the draw if the tick brought no new data. Ticks that update every row will still repaint the table, but quiet ticks won't.
- **Keep rows where they are.** Re-sorting or scrolling on every update moves every row, so every cell changes. Keep the user's selection and sort order fixed while the data updates.
- **Only build rows that are on screen.** For large datasets, create `Row`s for the visible slice and track the offset yourself. Building 10k `Row`s on each tick makes each frame slower, and slow frames tear more.
- **Write each frame in one go.** Without mode 2026, the terminal can show half a frame if it arrives in many small writes. Wrapping stdout in a large `BufWriter` (e.g. `CrosstermBackend::new(BufWriter::with_capacity(1 << 16, io::stdout()))`) lets Ratatui's flush send the frame in far fewer writes. If you do this, send the begin/end sequences through `terminal.backend_mut()`, as above, so they stay in order with the frame. The panic hook's direct write to stdout can then reach the terminal before frame bytes still sitting in the `BufWriter`. That's harmless, because the end sequence still gets out and releases the screen. Hide the cursor while drawing.

## How to check it

1. In kitty and WezTerm, compare with and without `draw_synced` while the table updates at its worst rate.
2. Add a debug flag that makes a cell panic. Confirm the shell comes back right away, with no 2-second freeze in kitty.
3. Add one PTY end-to-end test that captures the output stream and checks that every `\x1b[?2026h` has a matching `\x1b[?2026l`, including on the error and panic exits.

If you share the table layout, I can also check how much of the screen goes to borders and labels instead of data, and how it holds up at 80×24 and in a 60-column tmux split.
