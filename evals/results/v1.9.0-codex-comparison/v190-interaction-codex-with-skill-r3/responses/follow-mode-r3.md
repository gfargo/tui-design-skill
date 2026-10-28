**Auto-scroll should stop as soon as the user scrolls up, and resume only when they explicitly return to live output.** Use two visible states:

| State | Behavior |
|---|---|
| **FOLLOWING** — default on open | Pin to the bottom; new lines scroll into view. |
| **PAUSED** — reading history | Hold the viewport steady while logs keep arriving. Show `37 new` and a resume hint. |

Recommended controls:

- `↑`, `k`, `PgUp`, `Home`, or wheel up pauses following.
- `End` / `G` jumps to the latest line and resumes following.
- `F` toggles follow; enabling it jumps to the bottom.
- Ordinary downward scrolling stays paused until the user explicitly resumes. Never resume on a timer.

Keep the reading position anchored to a **stable log-entry ID**, with an offset within wrapped entries. Appends and resize should preserve that anchor. If buffer eviction removes it, show `Older entries expired` and move to the earliest retained entry.

Make the state clear in one compact footer:

```text
Wide
12:04:31 INFO  Request completed: GET /api/orders
PAUSED · 37 new                 End/G resume  / search  ? help

60-column split
12:04:31 INFO  Request completed: GET /api/orders
PAUSED · 37 new   End/G resume
```

At 80×24 and 60 columns, keep the log pane and state/resume hint; hide secondary hints first. Use zero nested borders, one textual state indicator, and one footer row—no repeated pause markers or blinking badges.

Filters should preserve the current follow state; while paused, count new **matching** entries. Keep connection status separate: `PAUSED` means scrolling stopped, while `DISCONNECTED` means ingestion stopped.