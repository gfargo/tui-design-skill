**Follow by default, and stop following as soon as the user scrolls up.** The viewer has two states, and the user should always be able to see which one it's in:

| State | Enter it by | Behavior |
|---|---|---|
| **Following** (default on open) | Opening the view, `G` / `End`, or `F` | The view stays at the bottom and new lines scroll in |
| **Paused** | Any upward move: `k`, `↑`, `PgUp`, `Ctrl+U`, `g`, wheel up | The view holds still and new lines pile up off-screen with a visible count |

### The rules that matter

1. **Scrolling up pauses following.** Don't make the user press a "pause" key before they can read. The scroll itself is the request to stop.
2. **Keep the view still while paused.** Anchor it to the line ID at the top of the screen, not to a row offset. Then new lines at the bottom don't shift anything. If the ring buffer drops old lines from the top, the text still doesn't jump. This is the same "don't scroll under the cursor" rule that applies to any live list.
3. **Show the backlog.** Put something like `▾ 37 new` in the corner and update it as lines arrive. The user can see the stream is still running and how far behind they are.
4. **Make it easy to re-pin.** `G` jumps to the end and resumes following. `F` toggles following, as in `less`. Scrolling back down to the last line should also resume it. That last one is my suggestion rather than an established rule, but people expect it.
5. **Show the state in text, not only color.** Use `● FOLLOW` / `‖ PAUSED` in the title or footer so it survives `NO_COLOR`.
6. **Filtering doesn't change the state.** With a filter active, new lines that match still flow in (or add to the count while paused), and the match count updates.

### Supporting decisions

- **Ring buffer:** keep the last 10k–100k lines and say when old ones are dropped (`oldest 52,310 lines dropped`). Offer to write the full stream to a file.
- **Wrap toggle (`w`):** wrap prose logs by default. For JSON or columnar logs, default to no wrap: cut lines with `…` and scroll sideways.
- **Search vs. filter:** `/` with `n`/`N` searches and moves the view, which pauses following. A filter narrows which lines show and leaves the state alone.

### Layout

Wide (100+ columns):
```
┌ api-server logs ─────────────────────────────── ‖ PAUSED  1,204/1,241 ┐
│ 12:04:01 INFO  request id=8f2 path=/users status=200 12ms             │
│ 12:04:01 WARN  slow query table=orders 840ms                          │
│ 12:04:02 ERROR upstream timeout host=billing                          │
│ ...                                                                   │
│                                                          ▾ 37 new     │
└───────────────────────────────────────────────────────────────────────┘
 G follow  F toggle  / search  w wrap  q back
```

60 columns (tmux split):
```
api-server ‖ PAUSED                          ▾ 37 new
12:04:01 INFO  request id=8f2 path=/users st…
12:04:02 ERROR upstream timeout host=billing
...
G follow  / search  w wrap  ? more
```
At 60 columns, drop the border and the position count, and keep only the state label and backlog count. The footer keeps the re-pin key (`G`) and moves the rest behind `?`. Those two are the only parts of the status that are essential.

**Clutter check:** encode the state once, as the text label (plus color if you want). Don't add a separate icon, a border color change, *and* a banner. The `▾ N new` count only appears while paused, so it carries meaning instead of becoming permanent noise.

**Test** the state machine without a terminal: send these synthetic events and check the state, the anchor line, and the backlog count:
- scroll up
- append 50 lines
- ring-buffer drop
- `G`

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink), I can point to its built-in support. For example, Textual's `anchor()` already pins a container to the bottom until the user scrolls up.
