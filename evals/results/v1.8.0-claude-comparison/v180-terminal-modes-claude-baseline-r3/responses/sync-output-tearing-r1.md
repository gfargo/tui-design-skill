Yes. The feature is **Synchronized Output**, DEC private mode **2026**. You send "begin synchronized update" (`CSI ? 2026 h`), write the whole frame, then send "end synchronized update" (`CSI ? 2026 l`). The terminal holds back rendering until the end marker arrives and then shows the frame all at once. kitty and WezTerm both support it, as do Ghostty, foot, Alacritty, iTerm2 and recent Windows Terminal. Terminals that don't know the mode just ignore it, so it's safe to always send.

I didn't find any Rust sources in this directory, so the code below is the general pattern and isn't fitted to your app.

## Using it with Ratatui and crossterm

crossterm has commands for both markers. Ratatui's `draw()` doesn't add them for you, so wrap each frame yourself:

```rust
use crossterm::{execute, queue, terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate}};

fn draw_frame<W: std::io::Write>(
    terminal: &mut ratatui::Terminal<ratatui::backend::CrosstermBackend<W>>,
    app: &App,
) -> std::io::Result<()> {
    // Queued, so it goes out in the same flush as the frame
    queue!(terminal.backend_mut(), BeginSynchronizedUpdate)?;
    let res = terminal.draw(|f| ui(f, app));
    // Always end the update, even if draw failed
    execute!(terminal.backend_mut(), EndSynchronizedUpdate)?;
    res.map(|_| ())
}
```

## Using it safely

1. **Always send the end marker.** Send it even when `draw` returns an error, as the code above does. Also put `EndSynchronizedUpdate` in your panic hook and restore path, next to `LeaveAlternateScreen` and `disable_raw_mode`. Terminals do time out a stuck update after a short delay, but don't rely on that.
2. **Keep each begin/end pair around one frame only.** Never leave an update open while you wait for input, sleep until the next tick, or do slow work. While it's open the screen looks frozen.
3. **Don't nest updates or spread one across ticks.** Use one begin, one frame and one end.
4. **Detecting support is optional, and the query has a catch.** You can ask with DECRQM (`CSI ? 2026 $ p`); the reply is `CSI ? 2026 ; 1|2 $ y` if it's supported. But the reply comes back on stdin, and crossterm's event reader can misread it as keypresses. Only query before your event loop starts, or skip the query, since sending the markers unconditionally is fine.
5. **tmux and other multiplexers** have their own support for this, which depends on the version. Test inside tmux if your users run the dashboard there.

## Also reduce the amount of output per frame

Synchronized Output hides tearing, but it doesn't make a frame cheaper to draw. Check these too:

- **Don't call `terminal.clear()` every tick.** It throws away Ratatui's diffing, so every frame redraws the entire screen.
- **Only redraw when data actually changed**, not on every tick.
- **Buffer stdout.** Wrap it as `CrosstermBackend::new(BufWriter::new(stdout()))` so a frame goes out in a few large writes instead of many small ones.
- **Keep row order stable.** If table rows reorder or scroll every tick, most cells change and the diff is large. Stable ordering keeps each update small.

With the begin/end wrapper and fewer full redraws, the tearing in kitty and WezTerm should go away.
