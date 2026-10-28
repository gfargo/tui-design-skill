The flicker comes from repainting the whole screen. Fixing that solves most of it, and synchronized output handles the rest.

## Why it flickers in tmux

tmux sits between your app and the real terminal. It reads your output, updates its own copy of the pane, and redraws that to the outer terminal on its own schedule. If each frame starts with a clear (`CSI 2J`, `terminal.clear()`, `tea.ClearScreen`, and so on) and then repaints everything, tmux can redraw while the pane is still half-blank. You see the blank as a flash. A full repaint is also more bytes per frame, so the half-drawn state lasts longer, and over SSH it lasts much longer.

## What to do, in order

1. **Stop clearing the screen every frame.** Clear only on resize or when you come back from a suspend or editor handoff. Every other frame should overwrite cells in place.

2. **Send only the cells that changed.** Keep the previous frame in memory, compare it to the new one, and write just the differences. Most frameworks already do this, so if you're on one, check that nothing is forcing a full repaint:
   - **Ratatui:** call `terminal.draw()` and nothing else per frame. `terminal.clear()` throws away the diff, so the next draw repaints every cell. Keep it for resize and resume.
   - **Bubble Tea:** don't return `tea.ClearScreen` from `Update` on routine messages.
   - **Ink:** set Ink 8's `incrementalRendering: true` so it rewrites only the changed part of each line.
   - **A hand-rolled renderer:** you need a frame buffer and a diff. Without them, steps 3–4 only partly help.

3. **Write each frame in a single `write`.** Build the whole frame in a buffer and flush once. Many small writes give tmux a chance to redraw between them.

4. **Wrap each frame in synchronized output (mode 2026).**
   ```
   CSI ? 2026 h   … frame bytes …   CSI ? 2026 l
   ```
   The terminal holds the screen until the end marker arrives, so a half-drawn frame is never shown. **tmux supports this from 3.7**, so check `tmux -V`. Some frameworks handle it for you:
   - Bubble Tea v2: on when the terminal reports support (over SSH, only if `TERM` names a known terminal)
   - Textual: on when the terminal reports support (full-screen only, never inline)
   - Ink 8: always on when attached to a terminal
   - crossterm/Ratatui: **you add it yourself**. Send crossterm's `BeginSynchronizedUpdate`/`EndSynchronizedUpdate` commands before and after `draw()`.

   **Always send the end marker, including on error paths.** If it's missing, the screen freezes until the terminal's timeout releases it, which can be 150 ms to 2 s. Support is optional, so you can check with DECRQM (`CSI ? 2026 $ p`), and steps 1–3 still need to work without it.

5. **Hide the cursor while you draw.** Show it again afterwards on the focused row or field. Otherwise it visibly jumps across the screen during every frame.

6. **Render less often.** Redraw only when there's input, new data, a resize, or a timer you set on purpose. Never redraw unchanged state in a loop. If updates arrive in bursts (log tailing, streaming tokens), combine them and cap the frame rate. Ink's `maxFps` defaults to 30, and 15–30 fps is plenty for a dashboard.

## How to check the fix

- Run it in tmux 3.7+ and also in an older tmux or over SSH, where 2026 may not get through. After steps 1–3 it should look acceptable even without synchronized output.
- Log how many bytes each frame writes to a file, not to the screen. A keypress that moves the selection should write a few hundred bytes, not a whole screen's worth.
- Test resizing separately. That's where you still clear and repaint fully, and it should be the only time the screen flashes.

Which framework are you using, or did you write your own renderer? I can point you to the exact place where the full repaint is happening.
