No—use an **app-owned refresh scheduler**, with different sampling intervals only where needed.

The premise about btop needs correcting: the skill’s btop reference describes **one shared, configurable `update_ms` interval, defaulting to 2000ms**, rather than separate CPU and process timers. Widgets independently own focus, scrolling, and graph history.

For your dashboard:

- Start with a shared refresh clock for cheap data sources.
- If CPU sampling needs 100ms and process collection needs 2s, register those deadlines with the scheduler. Different cadences don’t require widget-owned timers.
- Run expensive collection asynchronously, deliver results to application state, and coalesce redraws. Keep one owner of terminal rendering.
- Prevent overlapping collections and skip missed ticks instead of accumulating work. Handle keyboard input immediately, regardless of sampling intervals.

**Sampling and rendering are separate:** moving the process selection should redraw immediately using cached data, without waiting for another process scan.

Give a widget a separate cadence when its source warrants it—not simply because it is a separate box.