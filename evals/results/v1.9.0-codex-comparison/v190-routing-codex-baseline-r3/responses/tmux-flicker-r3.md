Switch from full-screen redraws to **buffered, incremental rendering**.

- Keep a buffer of the last rendered screen. Build the next frame in memory, compare them, and write only changed cells or lines.
- Avoid clearing the screen (`clear`, `ESC[2J`) on each update. Overwrite changed regions, including spaces where text disappeared.
- Batch cursor moves, style changes, and text into one output buffer, then flush once per frame.
- Coalesce rapid updates and cap rendering at a reasonable rate, such as 30–60 fps. Skip frames when nothing changed.
- Enter the alternate screen and hide the cursor once at startup; restore both on exit.

If your TUI library supports **synchronized output** (DEC mode 2026), enable it through the library. With a compatible tmux and outer terminal, it prevents partially drawn frames from being displayed. Treat it as an addition to incremental rendering.

Also check that `$TERM` inside tmux accurately describes tmux—usually `tmux-256color` with matching terminfo installed. Don’t force it to `xterm-256color`.

The biggest improvement usually comes from removing the per-update clear and batching each frame into a single flush.