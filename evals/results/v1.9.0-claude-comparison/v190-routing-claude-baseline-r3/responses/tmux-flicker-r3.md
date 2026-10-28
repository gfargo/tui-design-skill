There's no code in this directory, so here's the general fix. If you tell me your language or library, I can be more specific.

## Why it flickers

Redrawing everything usually means clearing the screen (`\x1b[2J` or `clear`) and then writing every cell again. tmux sits between your app and the real terminal. It parses your output, updates its own copy of the screen, and then redraws the outer terminal. If the outer terminal shows a frame between the "clear" and the "repaint", you see a blank or half-drawn screen. That's the flicker. tmux makes the gap more likely because it adds a layer and may send the update in several chunks.

## Fixes, most important first

1. **Stop clearing the screen every frame.** Keep a buffer of what's currently on screen and build the next frame in a second buffer. Compare the two and only send output for the cells that changed: move the cursor there and write the new text. Then swap the buffers. This one change usually fixes it. Use `\x1b[K` (erase to end of line) only where a line got shorter.

2. **Send each frame in one write.** Collect the whole frame's output in memory and flush it once. Many small writes (one per cell or per line) let tmux and the terminal show partial frames. Watch out for unbuffered stdout or a flush after every print.

3. **Use synchronized output (DEC mode 2026).** Wrap each frame like this:
   ```
   \x1b[?2026h   ...frame output...   \x1b[?2026l
   ```
   The terminal holds the display until the frame is complete. Recent tmux versions understand this. To have tmux use it with the outer terminal, add this to `~/.tmux.conf` (adjust the pattern to match your outer `$TERM`):
   ```
   set -as terminal-features ',xterm*:sync'
   ```

4. **Hide the cursor while drawing.** Send `\x1b[?25l` before the frame and `\x1b[?25h` after it (or keep it hidden the whole time). This stops the cursor from visibly jumping around.

5. **Use the alternate screen.** Send `\x1b[?1049h` on startup and `\x1b[?1049l` on exit, so you're not scrolling the normal buffer.

6. **Only render when something changes, and cap the rate.** Mark the screen as dirty when state changes and draw at most about 30–60 times per second, rather than on every event or timer tick.

7. **Check your tmux setup.** Set `default-terminal` to `tmux-256color` (or `screen-256color`). Make sure the outer terminal is a modern one that supports mode 2026, such as kitty, WezTerm, iTerm2, Ghostty, Alacritty or foot.

## If you're using a library

- **ratatui, bubbletea, tcell, notcurses, Textual and curses** already compare frames. Flicker with these usually comes from calling something like `clear()` or a forced full repaint every frame. Remove that call.
- **Ink (React for CLIs)** has a history of repainting everything. Upgrade it, and keep frequently changing output (spinners, logs) small or move it into `<Static>`.
- **Your own renderer:** fixes 1–3 are the important ones.

If you share your render loop or tell me which stack you're on, I can point to exactly what to change.
