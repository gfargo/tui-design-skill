No—start with an **app-owned scheduler**, with independent widget state.

The premise needs correcting: btop shares one configurable refresh interval, `update_ms` (default **2000 ms**), across its boxes. Independent focus, scrolling, and graph history don’t imply independent timers.

If your app needs CPU samples every 100 ms and processes every 2 s:

- Track each data source’s next deadline in one scheduler.
- Collect asynchronously, keeping input and rendering responsive.
- Prevent overlapping collections; skip missed deadlines instead of queuing catch-up work.
- Deliver results as events and coalesce redraws when state changes. Keyboard input should update immediately.

**Sampling cadence and rendering cadence are separate.** A process table can repaint its selection immediately while retaining its latest 2-second data snapshot. Dedicated timers can suit isolated slow sources, but shouldn’t be every widget’s default.

For the dashboard layout, use one border per panel and remove repeated row decorations. At 80×24, prioritize processes with a compact CPU summary; at 60 columns, offer a single-pane view with panel switching and truncated columns. Show “terminal too small” below the minimum that keeps essential fields and controls usable.