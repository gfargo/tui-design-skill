The working directory is empty, so I can't see your code. This advice is general and works whatever framework you use. Redrawing the whole screen every frame is the cause. tmux makes it worse because it sits between your app and the real terminal: it parses everything you write, keeps its own copy of the screen, then redraws that to the outer terminal. A full clear-and-repaint leaves a moment where the screen is blank, and tmux often shows that moment.

## Fixes, most important first

**1. Don't clear the screen every frame.**
The usual cause is writing `\x1b[2J` (clear screen) or calling `clear()` before each redraw. Instead, move the cursor home with `\x1b[H` and overwrite in place. Clear only the leftover parts of lines with `\x1b[K` (erase to end of line). Use a full clear only on startup and on resize.

**2. Only send what changed (diff the frames).**
Keep two buffers in memory, the previous frame and the next one. Compare them cell by cell and only write the cells that differ, moving the cursor to each changed spot. ncurses, Ratatui, Bubble Tea, Textual, Ink and notcurses all do this for you. If you're using one of them, check that you aren't defeating it, for example by calling `clear()` / `terminal.clear()` / `Erase()` inside your render loop.

**3. Write each frame in one go.**
Build the whole frame in a buffer and send it with one `write()` and one flush. Many small writes let tmux show a half-drawn frame.

**4. Use synchronized output (DEC mode 2026).**
Wrap each frame like this:
```
\x1b[?2026h   ... frame bytes ...   \x1b[?2026l
```
The terminal holds the frame back until it's complete, then shows it all at once. tmux supports this from 3.4. Terminals that don't support it ignore the codes, so it's safe to always send them.

**5. Limit the frame rate.**
Don't redraw on every event. Mark the screen as needing a redraw and repaint at most about 30–60 times a second, or only when something actually changed.

**6. Use the alternate screen.**
Enter with `\x1b[?1049h` and leave with `\x1b[?1049l`. This keeps your app out of the scrollback and avoids scrolling side effects.

## tmux settings to check
```tmux
set -g default-terminal "tmux-256color"   # not "screen" or "xterm" inside tmux
set -sg escape-time 10                    # avoid input lag
set -ga terminal-features ",*:sync"       # tell tmux the outer terminal supports synchronized output (tmux ≥ 3.4)
```
Also check that `$TERM` inside tmux is `tmux-256color` or `screen-256color`. If terminfo is wrong, curses-style libraries fall back to full repaints.

## Quick way to see what's happening
Record your app's output and look at it:
```sh
script -q out.log ./your-app    # then: cat -v out.log | less
```
If `^[[2J` appears once per frame, that's the cause.

If you tell me the language and TUI library, or put the render loop in this directory, I can point to the exact lines to change.
