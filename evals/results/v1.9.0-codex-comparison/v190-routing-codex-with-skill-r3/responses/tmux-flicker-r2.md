**Replace clear-and-repaint output with buffered, differential rendering.** tmux can make the intermediate blank screen and partially drawn frames more visible.

Apply these changes in order:

1. **Send only changed cells.** Build the next frame in memory, compare it with the previous frame, and emit cursor movements, text, and styles only where needed. Your framework may already do this—check whether you’re forcing a clear or invalidating its whole buffer on every update.
2. **Batch each frame’s output.** Assemble the escape sequences and changes into one buffer, then write and flush once per frame. Keep logs out of the terminal the TUI owns.
3. **Render only when needed.** Redraw on input, changed data, resize, or intentional animation ticks. Coalesce rapid updates and skip unchanged frames.
4. **Use synchronized output when supported.** This lets the terminal present a completed frame together:
   ```text
   ESC[?2026h
   …frame updates…
   ESC[?2026l
   ```
   Query support with DECRQM (`ESC[?2026$p`) using a bounded timeout; don’t assume support because the outer terminal has it. tmux supports this from **3.7 onward**. Always send the closing sequence, including on error paths.
5. **Manage the cursor.** Hide it during drawing, then restore it at the focused field when appropriate. Restore terminal modes on exit.

Keep the alternate screen active for the session. Reserve full repaints for initial display, resize, resume, or recovery from screen corruption.

Verify inside and outside tmux, including an 80×24 window and a 60-column split. For a small data change, output should contain a small patch with no screen-clear sequence. Synchronized output helps prevent tearing; reducing emitted output addresses the underlying redraw cost.