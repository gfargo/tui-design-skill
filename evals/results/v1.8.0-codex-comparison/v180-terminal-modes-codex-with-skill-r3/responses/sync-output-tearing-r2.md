Yes—use **synchronized output**, DEC private mode **2026**. kitty and WezTerm support it: the terminal keeps displaying the previous frame while processing your updates, then presents the completed frame when you end synchronization. Ratatui’s buffer diffing reduces writes, but does not make their presentation atomic.

With Ratatui’s Crossterm backend, bracket each draw:

```rust
use ratatui::crossterm::{
    execute,
    terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate},
};

// Inside your rendering loop:
execute!(terminal.backend_mut(), BeginSynchronizedUpdate)?;

let draw_result = terminal.draw(|frame| app.draw(frame));

// Attempt the end even when draw returned an error.
let end_result = execute!(
    terminal.backend_mut(),
    EndSynchronizedUpdate
);

draw_result?;
end_result?;
```

Use these safeguards:

- **Probe support once:** send DECRQM, `ESC[?2026$p`; the reply is `ESC[?2026;Ps$y`. Values `1` and `2` mean supported and currently set/reset. Use a bounded timeout; unsupported or unanswered queries fall back to ordinary rendering. Route replies through one input owner so an event reader cannot consume them accidentally. Probe the actual connection, including tmux or SSH, rather than trusting `$TERM`.
- **Keep the bracket short:** prepare data before beginning; end and flush immediately after drawing. Never hold synchronization across input waits, network requests, or ticks.
- **Cover every exit path:** the example handles returned draw errors. Also arrange best-effort `EndSynchronizedUpdate` on panic, shutdown, suspend, and child-process handoff, before terminal restoration. Coordinate this with your existing panic cleanup; a guard alone runs after the panic hook. Terminal watchdog timeouts are recovery mechanisms, not cleanup guarantees.
- **Keep one output writer:** logs and concurrent terminal writes can corrupt a synchronized frame. Do not put these escape sequences inside Ratatui `Text` or `Span`.

Also stop drawing on ticks that change nothing. Render only visible table rows, cache expensive formatting, and avoid clearing the terminal every frame—Ratatui already emits changed cells. Synchronization fixes visible tearing; those changes reduce frame cost.

Verify in both terminals, directly and through your supported multiplexer, including a forced draw error and panic. Frame snapshots cannot verify terminal presentation.

[Protocol specification](https://github.com/contour-terminal/vt-extensions/blob/master/synchronized-output.md)