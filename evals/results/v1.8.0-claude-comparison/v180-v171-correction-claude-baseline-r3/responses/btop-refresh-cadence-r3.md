No. Also, btop doesn't actually work that way. It has one global `update_ms` setting (default 2000ms, minimum 100ms). On each tick a single runner thread collects CPU, memory, network and process data, then draws every box in one pass. The CPU graph looks smoother because it draws a new column each tick, not because it runs on a faster timer. So btop is an example of one central clock, not one timer per widget.

**Why one timer per widget causes problems in a TUI:**

- **Torn frames and flicker:** Timers fire at unrelated moments, so you end up writing partial screen updates. A full-screen dashboard should write each frame in one go.
- **Wasted wakeups:** Timers at 100ms, 250ms and 2s that never line up wake the process constantly. That costs idle CPU, which is embarrassing for a system monitor.
- **Sampling skew:** CPU percentage is a difference between two `/proc/stat` (or `host_processor_info`) readings. If each widget samples on its own, CPU, memory and process numbers come from different moments and won't add up.
- **Hard to control:** Pause, resize, changing the refresh rate and shutdown all have to reach N timers instead of one.

**Recommended structure:**

1. **One scheduler tick.** Use the greatest common divisor of the intervals you need, e.g. 100ms. Each widget declares its interval as a whole number of ticks: CPU = 1, processes = 20. On each tick, refresh only the widgets that are due.
2. **Keep data collection separate from rendering.** Collectors update a shared snapshot. Some sources should share one collector because they share a read: process CPU% and total CPU both need the same jiffies delta. Run slow collectors on a worker so they can't stall the UI. Process enumeration is the usual offender.
3. **Mark changed widgets dirty and draw once per frame.** After collection, redraw only the dirty widgets into a back buffer, diff it against the previous frame, and write the result in one flush. Ratatui, Bubble Tea and Textual already work this way, so let their render loop be your single frame.
4. **Let input trigger an immediate redraw** without forcing a data refresh. Scrolling the process list shouldn't re-read every process.
5. **Make the base interval configurable,** like btop, and skip collection while the app is suspended or hidden.

**When a separate timer is fine:** something that isn't really a widget refresh, such as a one-off toast that disappears after 3s or a debounce for search input. Even then, have it post an event to the main loop instead of drawing directly.

If you tell me which language or TUI framework you're using, I can sketch the scheduler loop for it.
