Treat background detection as an **optional, asynchronous hint**, never a startup prerequisite.

A good design is:

1. **Provide `light`, `dark`, and `auto` settings.** An explicit choice wins. In `auto`, render immediately with a documented fallback, then update if detection succeeds.

2. **Query without blocking.** Send the terminal’s OSC 11 background-color query through the existing terminal event loop. Give it a bounded deadline—perhaps a few hundred milliseconds—and keep processing input and rendering. SSH latency can delay replies; silence does not prove the terminal is unsupported. Don’t repeatedly retry unanswered queries.

3. **Parse replies as terminal protocol traffic.** Handle partial replies, both BEL and ST terminators, and supported RGB formats. Consume recognized replies so they don’t appear as keystrokes. A valid late reply can still update the theme. Skip queries when input/output aren’t connected to the interactive terminal.

4. **Subscribe to changes where supported.** Some terminals implement color-scheme notifications using private mode 2031. Detect support before enabling it, handle notifications in the same event loop, and restore any mode you changed on exit. If your palette follows the actual background, a notification can trigger a fresh OSC 11 query. Elsewhere, refresh on application resume or terminal focus, with throttling, and provide a manual refresh command.

5. **Keep terminal appearance separate from OS appearance.** OSC 11 reports the terminal’s default background, which may be explicitly configured and stay unchanged when the OS theme switches. Scheme notifications and OS-theme propagation also depend on the terminal and, over SSH, any multiplexer in between. There is no universally supported remote OS-theme signal.

For choosing light versus dark from RGB, use perceived luminance rather than a simple average of the channels. Keep the result stable near the cutoff, and redraw when it changes.

The resulting behavior should be: **instant startup, graceful fallback when replies never arrive, and automatic updates wherever the terminal exposes them.**