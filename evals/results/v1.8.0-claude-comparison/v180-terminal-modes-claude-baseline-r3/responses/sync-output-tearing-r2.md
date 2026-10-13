Yes. The feature is **synchronized output**, DEC private mode **2026**. Both kitty and WezTerm support it, and so do iTerm2, Ghostty, foot, Alacritty (0.13+), Windows Terminal, Contour, and tmux 3.4+.

I searched this directory and found no Ratatui code, so the snippets below are general.

## How it works

```
CSI ? 2026 h   →  begin synchronized update (terminal stops repainting)
... your frame's escape sequences ...
CSI ? 2026 l   →  end update (terminal shows the whole frame at once)
```

Between `h` and `l` the terminal keeps parsing your output but keeps showing the previous frame. When it gets `l`, it swaps in the finished frame in one go, so you never see half a table.

## Using it with Ratatui and crossterm

crossterm already provides the commands, so wrap each `draw`:

```rust
use crossterm::{execute, terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate}};

execute!(terminal.backend_mut(), BeginSynchronizedUpdate)?;
let res = terminal.draw(|f| ui(f, &app));
execute!(terminal.backend_mut(), EndSynchronizedUpdate)?;
res?;
```

Recent Ratatui versions may do this for you, so check your version's changelog for synchronized updates before adding your own wrapper. Nesting the begin/end pairs is harmless, but it's redundant.

## Using it safely

1. **Always send the end sequence, including on error paths.** Note that the code above calls `res?` only after `EndSynchronizedUpdate`, so an error in `draw` still ends the update. Never use `?` between begin and end. A guard type with `Drop` is cleaner:
   ```rust
   struct SyncGuard<'a, W: std::io::Write>(&'a mut W);
   impl<W: std::io::Write> Drop for SyncGuard<'_, W> {
       fn drop(&mut self) {
           let _ = crossterm::execute!(self.0, EndSynchronizedUpdate);
       }
   }
   ```
   Also send `EndSynchronizedUpdate` in your panic hook and terminal-restore code, next to `LeaveAlternateScreen` and `disable_raw_mode`. If your app crashes mid-frame without it, the screen looks frozen.

2. **Don't rely on the terminal's timeout.** Terminals give up on a sync update after a while (around 150 ms to 1 s depending on the terminal) and repaint anyway. That keeps a crashed app from freezing the screen for good, but an unended update still makes the screen stall and then tear. Keep the begin/end window to the frame write only. Don't do I/O, data fetching, or table building inside it. Build your data first, then begin, draw, and end.

3. **Unsupported terminals are fine.** Terminals that don't recognize a DEC private mode ignore it, so you can usually send the sequences unconditionally. To detect support, for example to log it or skip the wrapper, send DECRQM `CSI ? 2026 $ p`. The reply is `CSI ? 2026 ; Ps $ y`:
   - `Ps` = 1 or 2: supported
   - `Ps` = 0: not recognized
   - `Ps` = 4: permanently disabled

   Read the reply with a timeout, because some terminals never answer.

4. **Multiplexers:** tmux before 3.4 and older screen versions don't pass mode 2026 through, so users running your app inside them will still see tearing.

## Other causes worth checking

Sync output hides tearing but doesn't reduce the amount of work:
- **Buffer the backend.** Rust's `stdout()` is line-buffered, so use `CrosstermBackend::new(BufWriter::new(stdout()))`. That way each frame goes out in a few large writes instead of many small ones.
- **Don't call `terminal.clear()` every tick.** It defeats Ratatui's diffing and repaints every cell. Let `draw` diff against the previous buffer.
- **Only redraw when something changed**, or lower the tick rate for the large table. Then most ticks write nothing at all.

The biggest fix is usually sync output plus removing any per-tick `clear()`. If you share your draw loop, I can show exactly where these changes go.
