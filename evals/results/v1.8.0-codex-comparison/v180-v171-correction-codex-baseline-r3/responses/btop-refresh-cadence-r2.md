No—different refresh rates don’t require a timer per widget. A good default is **one scheduler, separate data collection rates, and one render loop**.

For a btop-style dashboard:

- Sample CPU data every **100ms**.
- Refresh process data every **2s**.
- Let widgets read the latest cached snapshots.
- Render when data or UI state changes, coalescing updates into one screen draw.

Track each collector’s next deadline with a monotonic clock, and sleep until the nearest deadline or an input event. Keep expensive collection off the UI thread so a process scan won’t stall input or CPU updates.

Widget-owned timers can be fine for a few independent components, but they complicate cancellation, testing, and coordinated rendering as the app grows. **Widgets should usually describe what they display; the scheduler should decide when their data updates.**