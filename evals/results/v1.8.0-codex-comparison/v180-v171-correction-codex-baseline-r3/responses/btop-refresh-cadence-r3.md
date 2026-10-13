No—different refresh rates don’t require a separate timer per widget. A good default is **one scheduler with per-source deadlines**.

Separate three concerns:

- **Sampling:** Collect CPU data every 100ms and process data every 2s.
- **State:** Store the latest results in a shared snapshot.
- **Rendering:** Redraw when data changes, coalescing updates into one frame.

The scheduler wakes for the earliest deadline, runs whatever is due, then schedules its next wake. Widgets display the latest state; they don’t own the collection timers. If several widgets use CPU data, they all share one sample.

Keep slow collection off the UI thread, and prevent overlapping polls—if a process scan is still running, skip the next tick rather than queueing more work. Use a monotonic clock for deadlines.

Independent timers are fine for a small prototype, but a central scheduler makes pausing hidden panels, changing refresh rates, and shutting down much easier.