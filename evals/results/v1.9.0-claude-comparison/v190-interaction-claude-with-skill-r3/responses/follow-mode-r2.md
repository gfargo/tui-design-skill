**Follow by default, and pause the moment the user scrolls up.** Any upward movement freezes the viewport exactly where it is. The user goes back to following on purpose, with `G` or `F`. Always show which state the viewer is in.

## The two states

| State | Entered by | Viewport | Indicator |
|---|---|---|---|
| **Following** (default on open) | Opening the viewer, `G` (jump to end), `F` (toggle, as in `less`) | Pinned to the bottom; new lines scroll in | `● FOLLOW` |
| **Paused** | `k`/`↑`, `PgUp`, `Ctrl+U`, `g`/`Home`, wheel up, starting a search | Doesn't move at all, whatever arrives | `‖ PAUSED  ▾ 37 new` |

The rules that make this feel right:

1. **Never move the text while someone is reading it.** In paused mode, track the top visible line by its sequence number, not by its row index. Otherwise the view drifts as lines are appended, or as old lines are dropped from the front of the buffer.
2. **Show the backlog in the paused state.** The `▾ 37 new` counter tells the user the stream is still alive and how far behind they are. Without it, a paused viewer looks like a frozen app.
3. **Going back to follow mode is always deliberate.** `G` jumps to the end and resumes following, and `F` toggles. I'd also resume following when the user scrolls down to the last line themselves, because that clearly means "I'm caught up." Moving down without reaching the end stays paused.
4. **Filters keep following.** New lines that match the filter appear, and the match count updates. A filter is not a pause.
5. **Search pauses.** `/` and jumping between matches are reading actions. So is selecting text with the mouse to copy it, so pause then too. Nothing is worse than a selection sliding away mid-drag.

## Layout

Wide (120 cols):
```
 api-server logs                                   ● FOLLOW   12,408 lines
 10:42:01.113 INFO  request completed  path=/v1/users status=200 dur=12ms
 10:42:01.140 WARN  slow query         table=orders dur=842ms
 10:42:01.201 INFO  request completed  path=/v1/orders status=200 dur=861ms
 …
 G end · F follow · / search · f filter · w wrap · ? help
```

Paused, at the 60-column floor:
```
 api-server  ‖ PAUSED ▾ 37 new        9,871/12,445
 10:41:12 WARN  slow query table=orders dur=8…
 10:41:12 INFO  request completed path=/v1/o…
 …
 G end · F follow · / search · ? help
```
At 60 columns, drop the milliseconds from the timestamps, cut the footer to its four main keys, and truncate long lines with `…`. Keep the state indicator and the new-line count at every width, because they are the whole point of this view. At 80×24 the wide layout fits as is.

Clutter check: show the state as a word plus a symbol (`FOLLOW`/`PAUSED`), and use color only to reinforce it. Don't add a border around the log body, because every column of chrome costs you a column of log text. Don't add a per-line "new" marker either. The single counter says the same thing.

## Supporting decisions

- **Wrap toggle (`w`):** wrap by default for prose logs. For JSON or columnar logs, start unwrapped: truncate with `…` and scroll sideways.
- **Ring buffer:** keep a fixed maximum number of lines (10k–100k is typical). Say when old lines are dropped: `oldest 52,310 lines dropped`. If the line the paused user was reading gets dropped, move the view to the oldest line still kept and say so; don't jump silently. Offer to write the full stream to a file.
- **Bursty input:** collect incoming lines on a background task and redraw on a short timer (~16–33 ms). Don't redraw for every line, and don't read the stream on the UI thread.
- **Position:** show `9,871/12,445` while paused, so the user knows how far they've scrolled.

## Tests

Unit-test the state machine without a terminal:
- Scrolling up switches to paused.
- New lines arriving while paused leave the view unchanged and only increase the counter.
- `G` and `F` resume following.
- Scrolling down to the last line resumes following.
- Dropping old lines while paused keeps the user on the same line.

Then snapshot both states at 80×24 and at 60 columns.

If you tell me your framework (Bubble Tea, Ratatui, Textual, Ink…), I can show how this maps onto its viewport and message model.
