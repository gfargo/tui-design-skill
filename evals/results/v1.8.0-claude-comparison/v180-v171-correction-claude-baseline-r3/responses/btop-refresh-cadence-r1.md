**Short answer: no.** Let each widget choose how often it updates, but run everything from one scheduler and draw one frame at a time.

**First, a correction about btop.** As far as I know, btop doesn't give each box its own timer. It has a single `update_ms` setting (default 2000ms, minimum 100ms). One collector thread gathers CPU, memory, network and process data on that interval, and then one render pass draws the whole screen. If you've seen the CPU graph look faster than the process table, that's probably a config or version difference, not separate timers per box. It's worth checking against the version you're copying.

## Why one timer per widget causes problems

- **Wasted redraws and flicker.** A terminal is one shared surface. If five timers each trigger a redraw, you can write to the terminal five times in a few milliseconds, or draw half-updated frames. You want one diffed write per frame.
- **Data races.** Each timer reads shared state like terminal size, focus, theme and layout at a different moment. A resize in the middle of a cycle leaves widgets drawn against different layouts.
- **Timer drift.** Separate intervals drift apart, so graphs that should line up (CPU next to network, say) slowly fall out of step.
- **Extra CPU use.** A monitoring tool that burns CPU or battery waking up constantly looks bad, because people will see it in its own process list.
- **Harder testing.** One clock is easy to fake in tests. N independent timers aren't.

## A better structure

```
          ┌─────────────── single tick (e.g. 100ms) ───────────────┐
          │                                                        │
 collectors (worker thread/tasks)          main/UI loop            │
  cpu:   every 1 tick   ──┐                                        │
  mem:   every 10 ticks ──┼──► shared state + dirty flags ──► render once if dirty
  procs: every 20 ticks ──┘    (snapshot/swap, not live mutation)  │
                                         ▲                         │
                         input / resize ─┘ (immediate redraw)      │
```

1. **Widgets declare their interval** (`interval = 100ms`, `2s`, etc.). They don't own a timer. The scheduler runs a widget's collector when `now - last_run >= interval`. The base tick can be the GCD of the intervals, or you can sleep until the next deadline due.
2. **Keep collecting separate from drawing.** Run collectors off the UI thread, especially slow ones like the process list (walking `/proc` or calling `sysctl`). They publish an immutable snapshot and mark their widget dirty.
3. **Render once per tick, and only if something changed.** Lay out the full frame, diff it against the previous one, and write once. Cap the frame rate (e.g. 30fps) no matter how many collectors fire.
4. **Input and resize skip the queue.** Keystrokes, scrolling and SIGWINCH trigger an immediate render using the latest snapshots, without waiting for the next data tick. That keeps the UI responsive even when the process table only refreshes every 2s.
5. **Don't block on slow collectors.** If the process scan is still running when its next turn comes, skip that turn instead of queueing another.

This gives you exactly what you described (fast CPU sparkline, slower process table) without the problems above. Most TUI frameworks already work this way: Bubble Tea's `tea.Tick` messages go into one update loop, Ratatui apps usually use one event loop with a tick event, and Textual's `set_interval` timers all run on one event loop and batch their refreshes.

If you tell me your language or framework, I can sketch the scheduler concretely.
