Yes—use **synchronized output**, DEC private mode **2026**. kitty and WezTerm support it. The terminal keeps displaying the previous frame while it processes your updates, then presents the completed frame when you end synchronization.

Ratatui’s buffer diffing reduces output, but those changed cells can still appear progressively. Synchronization addresses that visible tearing.

The protocol is:

```text
Begin frame: ESC [ ? 2026 h
End frame:   ESC [ ? 2026 l
```

With Ratatui’s Crossterm backend, wrap each `terminal.draw()`:

```rust
use std::io;
use ratatui::{DefaultTerminal, Frame};
use ratatui::crossterm::{
    execute,
    terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate},
};

fn draw_synced(
    terminal: &mut DefaultTerminal,
    render: impl FnOnce(&mut Frame),
) -> io::Result<()> {
    let draw_result = (|| -> io::Result<()> {
        execute!(terminal.backend_mut(), BeginSynchronizedUpdate)?;
        terminal.draw(render)?;
        Ok(())
    })();

    // Attempt End even if Begin or draw returned an error.
    // execute! also flushes the writer.
    let end_result =
        execute!(terminal.backend_mut(), EndSynchronizedUpdate);

    draw_result?;
    end_result
}

// At your existing draw site:
// draw_synced(terminal, |frame| app.draw(frame))?;
```

Use it safely with these rules:

- **Detect support once.** Send DECRQM `ESC[?2026$p`; the reply is `ESC[?2026;Ps$y`. Values `1` and `2` mean the mode is supported and currently set/reset. Use a bounded timeout and fall back on no reply or unsupported status. Route replies through the owning input parser; a second stdin reader can steal keys or responses. Don’t infer support solely from `TERM`, especially inside tmux or over SSH.
- **Always end the frame.** The example handles returned errors; it does **not** handle panics. Add best-effort `EndSynchronizedUpdate` plus flushing to your panic cleanup before terminal restoration and diagnostic output. Also reset it before suspend or subprocess handoff. Preserve Ratatui’s existing restoration hook.
- **Keep the interval short.** Prepare data before beginning; end before polling input, sleeping, awaiting, or doing network work. Terminal timeouts are a recovery mechanism, not cleanup—kitty can hold a stuck frame for about two seconds.
- **Keep one output owner.** Send logs to a file and prevent concurrent terminal writes from interleaving with frames.

Also stop redrawing unchanged state on every tick: mark the dashboard dirty on data, input, resize, or intentional animation changes. Keep table formatting and sorting out of the render path where practical. Synchronization improves presentation; it doesn’t reduce rendering cost.

Verify in kitty and WezTerm, through any supported multiplexer, and with synchronization disabled. Exercise draw errors and panics to confirm the display releases and terminal modes restore.

[Protocol specification](https://github.com/contour-terminal/vt-extensions/blob/master/synchronized-output.md)