**Replace clear-and-repaint with buffered, incremental rendering.** tmux can make the intermediate blank screen and partial redraws more visible.

1. **Diff frames.** Build the next frame in memory, compare it with the previous one, and emit only changed cells through your framework’s renderer. Avoid clearing the screen (`ESC[2J`) on every update. Full redraws belong at startup, resize, or recovery after terminal handoff.
2. **Batch output.** Buffer each frame’s cursor moves, styles, and text, then write and flush once. Keep logs out of the terminal the TUI owns.
3. **Render only when needed.** Update on input, changed data, resize, or intentional animation ticks. Coalesce rapid updates and skip unchanged frames.
4. **Use synchronized output when supported.** It holds presentation until the frame finishes:
   ```text
   ESC[?2026h
   <frame output>
   ESC[?2026l
   ```
   Prefer framework support. Otherwise query support with a bounded timeout and always send the closing sequence, including on errors. tmux 3.7+ supports this; older versions need the buffered-diff fallback.
5. **Manage terminal modes cleanly.** Enter the alternate screen once per session. Hide the cursor while drawing, restore it at the focused input when appropriate, and restore terminal state on exit.

Verify with the same workload outside and inside tmux (`tmux -V`), including rapid updates and pane resizing. **Incremental rendering is the primary fix; synchronized output further reduces tearing.**