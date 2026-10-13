No—**give data sources appropriate cadences, but keep scheduling and rendering coordinated.**

One correction: the skill’s btop case study describes a **shared configurable refresh interval** (`update_ms`, default 2000ms), rather than CPU at 100ms and processes at 2s. Independent widgets means independent focus, scroll, and history; it doesn’t require independent timers.

If your app needs those two rates, use:

- **One scheduler:** collect CPU every 100ms and processes every 2s, using per-source deadlines.
- **Background collection:** send results into the UI event loop; never block input or rendering. Allow at most one outstanding collection per source, skipping missed intervals instead of building a backlog.
- **One coordinated render path:** update cached state when results arrive and coalesce redraws. Handle input and resize immediately, without waiting for the next sampling deadline.

Separate timers can be reasonable for independently managed, expensive sources, but widgets should not each write to the terminal. Also distinguish **sampling rate from display rate**: repainting a graph faster doesn’t create fresher measurements.

For the dashboard itself, keep one border per panel and avoid repeated “refreshing” markers. At 80×24, prioritize processes with a compact CPU summary; at 60 columns, offer a single focused pane with switching. Show “terminal too small” below a tested minimum.