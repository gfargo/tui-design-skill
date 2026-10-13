Yes. The feature is **synchronized output, DEC private mode 2026**. You send `CSI ? 2026 h` before a frame and `CSI ? 2026 l` after it. The terminal holds the screen until the end marker arrives, then shows the whole frame at once. kitty, WezTerm, foot, Alacritty, Ghostty, iTerm2, Windows Terminal 1.23.20211+ and tmux 3.7+ all support it.

Ratatui doesn't turn it on for you. Bubble Tea, Textual and Ink handle it themselves, but in Ratatui your app has to send the sequences.

## Wrap each frame

crossterm, which Ratatui re-exports, has `BeginSynchronizedUpdate` and `EndSynchronizedUpdate` commands. `CrosstermBackend` implements `Write`, so you can queue them straight into the backend:

```rust
use std::io;
use ratatui::{DefaultTerminal, crossterm::{execute, queue,
    terminal::{BeginSynchronizedUpdate, EndSynchronizedUpdate}}};

fn draw_synced(terminal: &mut DefaultTerminal, app: &App) -> io::Result<()> {
    queue!(terminal.backend_mut(), BeginSynchronizedUpdate)?;
    let drawn = terminal.draw(|f| app.draw(f)).map(drop);
    // Always close the frame, even if draw failed, then report the first error.
    let ended = execute!(terminal.backend_mut(), EndSynchronizedUpdate);
    drawn.and(ended)
}
```

Replace `terminal.draw(...)` in your loop with `draw_synced(...)`.

## Safety rules

1. **Always send the end marker.** If it never arrives, the screen stays frozen until the terminal gives up: 2 s in kitty, 1 s in Ghostty, 150 ms in Alacritty. The snippet above handles errors. Capture the draw result instead of using `?` in the middle, or an error can skip the end.

2. **Cover panics too.** Ratatui's panic hook only undoes raw mode and the alternate screen. It doesn't touch anything you turned on yourself. Install your own hook after `ratatui::init()` so it runs first, then hand off to Ratatui's:
   ```rust
   let prev = std::panic::take_hook();
   std::panic::set_hook(Box::new(move |info| {
       let _ = execute!(std::io::stdout(), EndSynchronizedUpdate);
       prev(info); // Ratatui's hook: restore terminal, then color-eyre etc.
   }));
   ```
   A hook works even with `panic = "abort"`, where a `Drop` guard would never run. It also helps to keep the draw closure free of anything that can panic, like slicing or indexing on untrusted widths.

3. **Probing for support is optional for kitty and WezTerm.** Terminals that don't know a private mode ignore it, so sending it unconditionally is generally harmless. If you want to detect it, for example to log it or change your fallback, send DECRQM `CSI ? 2026 $ p`. A reply of `CSI ? 2026 ; 1 $ y` or `; 2 $ y` means it's supported. Probe once before you start the `EventStream` reader, so the reader doesn't swallow the reply. Use a short timeout, because some terminals and multiplexers never answer, and render normally while you wait.

4. **Close the frame before handing off the terminal.** If you suspend or launch `$EDITOR`, a frame must not still be open at that point. With `draw_synced` it never is, so keep it that way.

## Fix the cause too

Mode 2026 hides tearing but doesn't reduce what you send. Ratatui already compares each frame to the last and writes only the cells that changed. If a "large table" tears, a lot of cells are probably changing on every tick. Check these before relying on the mode alone:

- **Draw only when something changed.** The skill's rule is to render on input, data, resize, or a deliberate tick, not to redraw unchanged state every time. Have `on_tick` return whether the data changed, and skip the draw when it didn't.
- **Don't call `terminal.clear()` in the loop.** It forces every cell to be repainted. Only use it after a resize glitch or a terminal handoff.
- **Keep column widths stable.** If widths come from each tick's content (`Constraint::Min`/fit-to-content), one longer value shifts every column, and the whole table counts as changed. Use fixed or `Length` widths and truncate long values.
- **Keep the selection and scroll offset in a long-lived `TableState`** owned by your app struct. Re-sorting or re-anchoring every tick moves every row. If the data has many thousands of rows, build `Row`s only for the visible window rather than the full dataset.
- **Terminals without mode 2026:** the fallback is to write each frame in one `write`, send only changed cells, and hide the cursor while drawing. Ratatui does all three if you avoid the problems above.

One thing to test: in tmux below 3.7 the sequences don't reach the outer terminal. Try the dashboard inside tmux if your users run it there, because the tearing will come back unless the diff-size fixes above are in place.
