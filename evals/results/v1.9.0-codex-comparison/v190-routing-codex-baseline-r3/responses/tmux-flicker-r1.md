Switch from full-screen redraws to **diff-based rendering**: keep the previous frame in memory, build the next frame, and write only the cells or lines that changed.

Also:

- **Don’t clear the screen on each update.** Avoid `clear`, `ESC[2J`, or repeatedly leaving and entering the alternate screen.
- **Batch each frame’s output** into one buffer and flush once. Hide the cursor while the TUI runs.
- **Coalesce updates** so bursts of events produce one render. Skip rendering when nothing changed.
- **Use synchronized output when supported.** Wrap each frame in `ESC[?2026h` and `ESC[?2026l`. Support depends on both tmux and the outer terminal; feature-detect it and keep diff rendering as the fallback.
- **Check terminal configuration.** Inside tmux, `$TERM` should describe tmux—typically `tmux-256color`, with its terminfo installed—not `xterm-256color`.

If you use a TUI framework, use its buffered renderer and check that your update loop isn’t forcing a clear or recreating the terminal backend every frame. Diff rendering plus a single flush per frame is usually the biggest improvement.