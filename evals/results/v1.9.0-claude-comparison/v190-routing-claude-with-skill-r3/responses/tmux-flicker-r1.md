The fix is to stop clearing and repainting the whole screen. Inside tmux the gap between "clear" and "paint" is visible as flicker. I worked this out from the tui-design skill's terminal-protocols and ecosystem references.

## Do these in order

**1. Remove the clear from your render loop.** Look for `\x1b[2J`, `clear()`, `ClearScreen` or `erase()` running on every update. Keep a copy of the last frame, compare the new one against it, and write only the cells that changed. Every mainstream framework already does this for you if you don't force a clear:

- **Ratatui:** `terminal.draw()` already compares frames. Call `terminal.clear()` only after a resize glitch or after handing the terminal to `$EDITOR` or a shell, never once per loop.
- **Bubble Tea:** `View()` is compared automatically. Don't return `tea.ClearScreen` from a tick or from `Update`.
- **Ink:** use version 6.7 or later, which bundles each frame so it appears all at once. Ink 8's `incrementalRendering: true` rewrites only the changed part of each line. Lower `maxFps` (default 30), and use `<Static>` for logs that only grow.
- **Textual:** already does all of this. If it still flickers, look for code that writes to stdout directly.
- **Your own renderer:** keep a front buffer and a back buffer, compare them, and move the cursor only to changed cells.

**2. Send each frame with a single write.** Build the whole frame in one buffer and flush it once. Many small writes let tmux pass partial frames to the outer terminal.

**3. Wrap each frame in synchronized output (mode 2026)** where it's supported:

```
ESC[?2026h   … frame bytes …   ESC[?2026l
```

The terminal holds the frame and shows it all at once. Support for this inside tmux starts at **tmux 3.7**. Older versions don't forward it, so step 1 matters even more there. To check support, send the query `CSI ? 2026 $ p` and wait for the reply with a timeout. Always send the closing `l`, including on error paths. Otherwise the screen stays frozen until the terminal's own timeout, which is 150 ms to 2 s.

**4. Hide the cursor while drawing.** Show it again afterwards on the focused row or field so screen readers and users can still find it.

**5. Redraw only when something changes:** input, new data, resize, or a deliberate timer. A loop that redraws unchanged screens multiplies whatever flicker remains. If you're streaming logs or tokens, batch the updates.

## Quick checks

- Run `tmux -V`. Below 3.7, synchronized output won't get through, so diffing has to do the work.
- Run the app outside tmux in the same terminal. If it still flickers, tmux isn't the cause and the full-screen clear is.
- Inside tmux, `TERM` should be `tmux-256color` or `screen-256color`. A wrong `TERM` can make libraries use slower fallback output.
- Send debug output to a file. Anything printed to the screen the TUI is using forces a full repaint and looks like flicker.

If you tell me which language or framework you're using, or paste your render loop, I can point to the exact line causing the full repaint.
