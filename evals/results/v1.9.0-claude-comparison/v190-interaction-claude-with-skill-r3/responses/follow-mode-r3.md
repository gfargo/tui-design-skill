**Short answer:** open the viewer following the tail. Stop following the moment the user scrolls up, and keep the view still while they read. Show a visible "paused, N new" indicator. Resume only when they ask: `G`/`End`, `F`, or scrolling back down to the last line.

## The two-state model

| State | When | Viewport | Indicator |
|---|---|---|---|
| **Following** | Default on open | Stays at the bottom; new lines scroll in | `● FOLLOW` (or nothing, if paused is clearly marked) |
| **Paused** | Any upward move: `k`/`↑`, `PgUp`, `Ctrl+U`, `g`/`Home`, wheel up, starting a search | Frozen. New lines collect below without moving anything | `▾ 37 new · G to follow` |

The user should always be able to tell which state they're in. The common failure is a viewer that jumps back to the bottom while someone is reading a stack trace.

**Ways back to following:**
- `G` / `End` jumps to the bottom and resumes following.
- `F` toggles following, as in `less +F`.
- Scrolling down until the last line is visible resumes following. People expect this, and it saves a keypress.

## Rules that are easy to get wrong

1. **While paused, anchor the view to a line, not a row offset.** Pin the view to the ID or sequence number of the top visible line. If you store `scrollTop = 1200` and the buffer drops old lines from the front, the view drifts even though the user didn't touch anything.
2. **Use a ring buffer and say when it drops lines.** Keep 10k–100k lines and show `oldest 52,310 lines dropped`. If the line the user is reading gets dropped, snap to the oldest kept line and tell them. Don't jump silently.
3. **Filters keep following.** If a filter is active and you're following, new matching lines appear and the match count updates. If you're paused, the count of new matches still goes up.
4. **Search pauses.** Jumping to a match is reading, so stop following.
5. **Resize:** if following, stay at the bottom. If paused, keep the anchored top line in place. Re-wrapping changes row counts but shouldn't move what the user is looking at.
6. **Wrap toggle (`w`):** wrap by default for prose logs. For JSON or columnar logs, don't wrap: truncate with `…` and allow sideways scrolling.
7. **Bursts:** batch incoming lines and redraw at about 30 fps, not once per line. Do the reading off the UI thread.
8. **Mouse wheel** scrolls the pane under the pointer, and wheel-up pauses just like `k`.

## Layout

Wide (100+ cols):
```
 api-server logs                                   filter: error  · 142 matches
 12:04:31.220  INFO   request completed  path=/v1/users  status=200  dur=12ms
 12:04:31.981  ERROR  upstream timeout   path=/v1/orders retry=2
 12:04:32.004  WARN   pool near capacity used=48/50
 ...
 ⏸ PAUSED  ▾ 37 new                      w wrap  / search  F follow  G end  ?
```

Floor (60 cols, tmux split):
```
 api-server            ⏸ ▾37  1,204/9,880
 12:04:31 ERR upstream timeout path=/v1/o…
 12:04:32 WRN pool near capacity used=48/…
 ...
 G end  F follow  / search  ? help
```
At 60 columns, shorten timestamps to seconds, use 3-letter levels, and truncate the message instead of wrapping. The filter text moves into `?` help, and the position counter stays.

**Clutter check:** don't mark the paused state four ways (color, icon, word, border change). Use one status cell (`⏸ PAUSED ▾ 37 new`) plus a color, and leave the log area free of borders so the space goes to log lines. Show the follow/pause indicator in one place only, never on each row.

## Tests

Make the follow logic a pure state machine and unit-test it with synthetic events:
- Following plus append keeps the view at the bottom.
- Scrolling up then appending leaves the top line unchanged and increases the new-line count.
- Dropping old lines while paused keeps the anchored line in place.
- Scrolling back to the bottom resumes following.
- `G` resets the new-line count.

Then save golden frames at 80×24 and 60 columns in both states.

The skill doesn't need a specific framework for this answer. If you tell me yours, I can map it to that framework's API. In Textual, for example, `anchor()` on the scroll container already keeps the view at the bottom until the user scrolls up.
