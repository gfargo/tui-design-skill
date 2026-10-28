**Follow live output until the user scrolls up; then hold their reading position until they explicitly resume.** Use two visible states:

| State | New logs arrive | Transition |
|---|---|---|
| **FOLLOWING** — default on open | Keep the viewport pinned to the newest line | Up, PgUp, Home, or wheel up pauses following |
| **PAUSED** | Continue collecting logs; keep the visible text stationary; increment `37 new` | `End` or `G` jumps to latest and resumes; `F` toggles follow |

A few details make this predictable:

- **Never resume on a timer.** I’d also require explicit resume when ordinary downward scrolling reaches the bottom.
- Anchor paused content by stable line ID, preserving its screen position across appends and resize.
- Searching older logs pauses following. A live filter can keep following, showing incoming matches; label its backlog `37 new matches`.
- Bound retained history. If eviction removes the user’s reading position, show `Older lines expired` and anchor to the oldest retained line.
- Keep follow state separate from connection state: a disconnected source must say so.

Keep the state and resume action visible:

```text
Wide pane                            60-column pane
Logs: api-server                     Logs: api-server
14:32:01 INFO Request completed       14:32:01 INFO Request...
14:32:02 WARN Retry scheduled         14:32:02 WARN Retry...
PAUSED | 37 new | End latest | ? help  PAUSED | 37 new | End latest
```

At 80×24, keep one log pane and one footer row. At 60 columns, hide optional metadata before hiding the state or resume hint; collapse surrounding panels if needed. Below your declared minimum, show a truthful “terminal too small” message.

For clutter: use zero nested borders, one text state label, and no repeated per-row follow markers. In a 24-row view, a header and footer consume only 2 rows.

Verify three essential behaviors: incoming lines cannot move paused text, resume immediately shows the latest output, and resize or history eviction cannot silently jump the reader elsewhere.