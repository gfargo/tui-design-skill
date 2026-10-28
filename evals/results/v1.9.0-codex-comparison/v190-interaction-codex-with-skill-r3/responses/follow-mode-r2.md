**Follow new logs by default; stop auto-scrolling as soon as the user scrolls upward.** Keep their reading position steady until they explicitly resume.

| Event | Behavior |
|---|---|
| Open viewer | Follow the newest entries. |
| Up, PgUp, Home, or wheel up | Pause following immediately. |
| New entries while paused | Keep collecting; hold the viewport still; show `37 new`. |
| Down or PgDn while paused | Navigate without silently re-enabling follow. |
| End / G | Jump to newest and resume following. |
| F | Toggle follow; enabling it jumps to newest. |

“Paused” should mean **scrolling paused**, while ingestion continues. Never resume because a timer expires, focus changes, or the terminal resizes.

Keep the state and recovery action visible:

```text
Wide                                  60-column split
12:04:21 INFO request completed        12:04:21 INFO request completed
12:04:22 WARN retry scheduled          12:04:22 WARN retry scheduled
PAUSED | 37 new | End resume | ? help  PAUSED | 37 new | End resume
```

Use one log pane at 80×24 and 60 columns. Drop secondary metadata and hints before hiding the follow state or resume key. This needs zero added borders, zero per-row state markers, and one footer row—about 4% of an 80×24 screen. Plain text labels preserve meaning without color.

A few important edge cases:

- **Anchor by stable entry ID**, including the wrapped-line offset, so appends and resize don’t move the passage being read.
- **Search pauses following.** Filtering preserves the current follow/paused state; while following, matching new entries appear normally.
- **Bound retention.** If old entries are evicted, report it. If the reading anchor disappears, move to the oldest retained entry and explain why.
- **Keep connection status separate:** `Disconnected` and `Paused` describe different things.

Verify the core interaction: scroll up, append a burst of logs, and confirm the same passage stays in place while the new-entry count grows. Pressing End should then reveal the latest entry and restore following.