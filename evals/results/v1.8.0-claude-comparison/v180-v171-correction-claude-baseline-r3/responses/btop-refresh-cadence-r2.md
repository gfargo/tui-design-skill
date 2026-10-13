No. And the premise is a bit off: btop doesn't run boxes on separate timers. It has one `update_ms` setting (default 2000 ms, minimum 100 ms). Each tick, a single runner thread collects CPU, memory, network and processes, then draws all the boxes in one pass. Pressing keys or resizing triggers an extra redraw, but data collection still runs on the shared clock. It's worth checking your btop config, but I'm fairly confident it doesn't use per-box timers.

Even if you do want different rates per widget, separate timers are usually the wrong design.

## Problems with one timer per widget

- **Torn frames:** Each timer fires on its own, so you end up redrawing the screen several times per interval. That causes flicker and wasted terminal writes, and adjacent widgets can show data sampled at slightly different moments.
- **Drift and bunching:** Independent timers slide out of phase. Sometimes they all fire together and cause a CPU spike. Sometimes they spread out and the screen never settles.
- **Concurrency bugs:** If timers run on threads, you now need locking around shared state and the terminal buffer.
- **Hard to control globally:** Pause, "refresh now", changing the interval at runtime, and slowing down when the window is hidden all become N separate problems.
- **Duplicate collection:** Several widgets often read the same source (for example, `/proc/stat` feeds both a CPU graph and per-core meters). Separate timers read it more than once.

## Use one scheduler, many intervals

1. **One base tick**, for example 100 ms, or the greatest common divisor of the intervals you need.
2. **Each widget declares an interval**, such as `cpu: 100ms`, `procs: 2000ms`, `disk: 1000ms`. On each tick the scheduler runs only the collectors that are due (`now - last_run >= interval`).
3. **Collectors are separate from widgets.** Data sources update a shared model, and widgets subscribe to it. One read of `/proc/stat` serves every CPU widget.
4. **Dirty flags plus one render per tick.** Collectors mark widgets dirty, and at the end of the tick you draw only the dirty regions in a single buffered write. Input events also just mark things dirty.
5. **Slow collectors run in the background.** If a process scan takes 50 ms, run it on a worker and post the result back to the main loop. Then a slow source can't stall the fast CPU graph. This is the one place where something other than the main loop should own work, and it's a worker, not a timer.
6. **Use a monotonic clock and catch-up rules.** Schedule against `next_due += interval`, not "sleep the interval again", so timing doesn't drift. Skip missed ticks instead of running them in a burst after a stall.

Most TUI frameworks already work this way. Bubble Tea, Ratatui with an event loop, and Textual all have one loop with tick messages, so you're working with the framework rather than against it.

## Rates

A 100 ms CPU refresh looks smooth but costs real CPU in a terminal app. Something like 250–500 ms for graphs and 1–2 s for process tables is a common sweet spot. Making the base tick user-configurable, as btop does, is worth copying.

If you tell me your language or framework, I can sketch the scheduler loop concretely.
