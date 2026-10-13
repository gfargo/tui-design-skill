Yes. The feature is **Synchronized Output**, DEC private mode **2026**. You send `CSI ? 2026 h` (`\x1b[?2026h`) before a frame and `CSI ? 2026 l` after it. Between the two, the terminal keeps showing the previous frame. When the end marker arrives, it shows the new frame all at once, so you never see a half-drawn table. kitty and WezTerm both support it, as do Ghostty, foot, iTerm2, Alacritty, Windows Terminal and Contour. Terminals that don't recognise the mode ignore it, as they do with any unknown DEC private mode, so it's safe to send everywhere.

(Your working directory has no Rust sources, so this is general guidance rather than a patch to your code.)

## Using it with Ratatui and crossterm

Ratatui's `draw()` doesn't wrap frames in this mode for you, so add it around each draw. crossterm provides the commands:

```rust
use crossterm::{execute, terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate}};

fn render(terminal: &mut Terminal<CrosstermBackend<Stdout>>, app: &App) -> io::Result<()> {
    execute!(terminal.backend_mut(), BeginSynchronizedUpdate)?;
    let result = terminal.draw(|f| ui(f, app)); // draw() flushes the diff before returning
    // Always end the update, even if drawing failed
    execute!(terminal.backend_mut(), EndSynchronizedUpdate)?;
    result.map(|_| ())
}
```

## Using it safely

1. **Always send the end marker.** The code above ends the update even when `draw` returns an error. Also send it from your panic hook and your shutdown code, next to `LeaveAlternateScreen` and `disable_raw_mode`. For example: `let _ = execute!(io::stdout(), EndSynchronizedUpdate, LeaveAlternateScreen);`. Terminals give up waiting after a timeout (roughly 150 ms to 1 s, depending on the terminal), so a missing end marker won't freeze the screen forever. It will still cause stalls and visible glitches, though.
2. **Keep the begin/end window short.** Only drawing and flushing should happen inside it. Don't read input, do I/O or sleep between begin and end. If you do, you'll hit the timeout and get tearing anyway, plus added latency.
3. **Don't nest updates.** Use one begin/end pair per frame.
4. **Feature detection is optional.** You can ask the terminal with DECRQM by sending `\x1b[?2026$p`. A reply of `\x1b[?2026;1$y` or `;2$y` means it's supported, and `;0$y` means it isn't recognised. Most apps just send the markers unconditionally, because unsupported terminals ignore them.
5. **Multiplexers sit in between.** Under tmux or screen, it depends on the multiplexer whether the mode is handled or passed through. Recent tmux versions support it; older ones and screen don't. Test inside tmux if your users run there.

## Other causes of flicker to check

These often cause as much flicker as the lack of sync:

- **Don't call `terminal.clear()` every tick.** It throws away Ratatui's diffing and repaints the whole screen. Only call it after a resize or when the screen is corrupted.
- **Only redraw when something changed** (new data, input or resize), not on every tick. Or cap the frame rate.
- **Make sure each frame goes out in one write.** `draw()` flushes once at the end, so don't add your own flushes in the middle of rendering.

With synchronized output on and no full clears each tick, a large table should redraw cleanly in kitty and WezTerm.
