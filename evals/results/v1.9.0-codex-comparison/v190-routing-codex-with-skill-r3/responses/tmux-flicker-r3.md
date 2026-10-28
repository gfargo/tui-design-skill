**Replace clear-and-repaint with buffered, incremental rendering.** Clearing the screen on every update exposes a blank intermediate frame; tmux can make that more visible.

Apply these changes in order:

1. **Diff frames.** Build the next screen in memory, compare it with the previous screen, and emit only changed cells or runs. Prefer your framework’s renderer. Reserve full redraws for startup, resize, or recovery after terminal handoff.
2. **Batch output.** Assemble cursor moves, styles, and text into one output buffer per frame, then write and flush once. Avoid flushing per row or widget.
3. **Render only when needed.** Redraw on input, changed data, resize, or intentional animation ticks. Coalesce rapid updates and skip unchanged frames.
4. **Use synchronized output when supported.** It lets the terminal present a complete frame together:
   ```text
   ESC[?2026h    begin synchronized update
   …frame output…
   ESC[?2026l    end synchronized update
   ```
   Prefer framework support. Otherwise query support with `ESC[?2026$p`, use a bounded timeout, and always send the end sequence—even on errors. The skill lists native tmux support at **3.7+**; older versions need the incremental-rendering fallback.
5. **Keep terminal ownership clean.** Enter the alternate screen once per session. Hide the cursor during drawing, restore it where needed, and route logs to a file or framework console.

Compare the same workload outside tmux and inside it, checking `tmux -V`. Verify that an idle UI emits no frames and changing one value produces a small update. Synchronized output helps hide intermediate drawing, but reducing unnecessary output is the primary fix.