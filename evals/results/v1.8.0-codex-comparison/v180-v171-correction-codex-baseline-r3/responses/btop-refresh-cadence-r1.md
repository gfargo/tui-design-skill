No—give widgets independent **refresh rates**, but usually let a central scheduler manage them.

Separate three concerns:

- **Collection:** Sample CPU every 100ms and processes every 2s. Cache the latest results.
- **Rendering:** Redraw widgets when their data, layout, or interaction state changes. Coalesce updates into one terminal frame.
- **Scheduling:** Track each collector’s next deadline using a monotonic clock, then sleep until the earliest deadline or a user event.

This preserves different cadences without every widget owning a timer. It also makes pausing, changing refresh rates, and shutting down easier.

Keep slow collection off the UI loop, and avoid overlapping polls: if a process scan is still running when its next deadline arrives, skip that poll. After a delay, skip missed intervals rather than trying to catch up.

Per-widget timers are fine for a small prototype, but widgets should ideally consume data and render; the app should own scheduling.