Switch from full-screen redraws to **buffered, incremental rendering**:

- Keep the previous frame in memory, compare it with the new frame, and write only changed cells or lines.
- Avoid clearing the screen (`clear`, `ESC[2J`) on each update. Use cursor positioning to overwrite changed regions, including spaces where text was removed.
- Assemble each update into a single output buffer and flush once per frame. Coalesce frequent updates and cap rendering around 30–60 FPS.
- Hide the cursor while the TUI is active, and restore it on exit.

For tmux specifically, **synchronized output** can further reduce flicker: wrap each frame with `ESC[?2026h` and `ESC[?2026l` when supported by your terminal and tmux version. It helps display a frame atomically, but incremental rendering should still be the primary fix.

Also check that `$TERM` inside tmux is appropriate—typically `tmux-256color` with matching terminfo installed—and let your TUI library handle terminal capabilities. Don’t force `TERM=xterm-256color` inside tmux.

If you’re using a TUI framework, check whether it already provides diff rendering; bypassing its renderer with direct stdout writes can cause flicker too.