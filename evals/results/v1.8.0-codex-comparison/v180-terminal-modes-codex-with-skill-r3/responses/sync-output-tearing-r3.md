Yes—use **synchronized output, DEC private mode 2026**. kitty and WezTerm support it. The terminal continues processing your output but holds the visible frame until you end the update, preventing partial table redraws from appearing.

The sequences are:

```text
Begin: ESC [ ? 2026 h
End:   ESC [ ? 2026 l
Query: ESC [ ? 2026 $ p
```

Ratatui already diffs its frame buffers and writes changed cells; synchronized output makes that stream appear as one visual update. With the Crossterm backend, bracket the **whole `terminal.draw()` call**, not just the render closure:

```rust
use std::io;
use ratatui::{
    DefaultTerminal,
    crossterm::{
        execute,
        terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate},
    },
};

fn draw_frame(
    terminal: &mut DefaultTerminal,
    app: &App,
    synchronized: bool,
) -> io::Result<()> {
    if !synchronized {
        return terminal.draw(|f| app.draw(f)).map(|_| ());
    }

    // Attempt End even if Begin or draw returns an error.
    let draw_result = (|| {
        execute!(terminal.backend_mut(), BeginSynchronizedUpdate)?;
        terminal.draw(|f| app.draw(f)).map(|_| ())
    })();

    let end_result =
        execute!(terminal.backend_mut(), EndSynchronizedUpdate);

    draw_result.and(end_result)
}
```

Use it safely with these rules:

- **Probe once, with a timeout.** DECRQM replies look like `CSI ? 2026 ; Ps $ y`: `Ps=1` or `2` reports supported, set or reset. Treat no reply or unsupported status as fallback. Parse replies through your single input owner; a competing stdin reader can steal keys or capability responses. Probe the actual terminal path, including tmux or SSH, rather than trusting the outer emulator’s name.
- **Keep the bracket short.** Update data and do expensive computation beforehand. Never wait for input, sleep, perform network work, or await tasks between Begin and End. Serialize terminal writes through one owner.
- **Cover panics and handoffs too.** The example handles returned errors, but panics need an explicit best-effort End-and-flush **before** terminal restoration and panic reporting. Add that to your existing cleanup path; Ratatui’s managed cleanup does not own this custom mode. Also end it before suspend or launching an interactive child. An unwind guard alone runs after the panic hook, so it cannot protect the hook’s output.
- **Do not rely on the terminal watchdog.** kitty eventually releases a stuck update after roughly two seconds; that is recovery, not normal frame handling.

Also stop redrawing on ticks that do not change visible state. Keep Ratatui’s diffing, avoid clearing the screen every frame, and limit table preparation to visible rows. On unsupported terminals, use buffered frame output and hide the cursor while drawing.

Verify normal redraws, injected draw errors, and panic cleanup in kitty and WezTerm, plus your multiplexer path if used. `TestBackend` checks frame contents but cannot verify presentation tearing.

Protocol reference: [synchronized-output specification](https://github.com/contour-terminal/vt-extensions/blob/05050a11e793c8f4362bf4e34a59ed3f7e5105fe/synchronized-output.md).