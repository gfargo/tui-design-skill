The fix is to stop repainting the whole screen. Send only the cells that changed, and send each frame as one atomic write. tmux makes full redraws especially visible: it parses everything your app outputs into its own grid, then repaints the real terminal on its own schedule. If a frame arrives as "clear, then redraw", tmux can catch it halfway and show the blank state.

I didn't find any code in the working directory, so this is general advice. Share the relevant code or tell me which library you use and I can be more specific.

## 1. Stop clearing the screen
- Don't send `\e[2J` (clear screen) or `\e[H\e[J` before each frame. That's the most common cause of flicker.
- Move the cursor and overwrite text in place. Use `\e[K` to clear only the leftover end of a line that got shorter.

## 2. Diff frames (double buffering)
Keep two buffers: the frame currently on screen and the one you're about to draw.

```
for each cell (row, col):
    if next[row][col] != current[row][col]:
        move cursor (skip if it's already there)
        set style (only if it differs from the last style you sent)
        write the character
swap buffers
```

This usually cuts output by 90% or more, which removes most of the flicker without anything else. Most TUI libraries already do this, including ncurses, ratatui, tcell, notcurses, and Textual. If you're on one of them and still flicker, look for code that calls `clear()` and forces a full repaint every frame. In ncurses, for example, use `erase()` + `refresh()` instead of `clear()`.

## 3. Send each frame in one write
Collect the whole frame's escape sequences in a buffer and pass it to the terminal with a single `write()`. Many small unbuffered writes give tmux more chances to render a half-finished frame.

## 4. Use synchronized output (mode 2026)
Wrap each frame in these sequences:

```
\e[?2026h   ... frame output ...   \e[?2026l
```

The terminal (and recent tmux) holds the display until the frame is complete and then shows it all at once. Terminals that don't support it ignore the sequences, so it's safe to always send them. To make tmux forward sync to your outer terminal, add this to `~/.tmux.conf`:

```
set -as terminal-features ',xterm-256color:sync'
```

Replace `xterm-256color` with your outer terminal's `$TERM`. Check your tmux version with `tmux -V`. Older releases may not support this, and upgrading helps.

## 5. Smaller fixes
- **Hide the cursor while drawing** (`\e[?25l`) and show it again afterward (`\e[?25h`), or just leave it hidden.
- **Limit the frame rate.** Combine many updates into one frame at 30–60 fps at most, instead of redrawing on every event.
- **Use the alternate screen** (`\e[?1049h` / `\e[?1049l`) for full-screen apps.
- **Set `TERM` correctly inside tmux.** It should be `tmux-256color` or `screen-256color`, not your outer terminal's value. A wrong terminfo entry can make libraries choose slow or broken redraw methods.

## Order to try them
Diffing plus one write per frame fixes most cases. Synchronized output removes the tearing that's left. If you're using a library and it still flickers, tell me which one and I'll point you to its specific cause.
