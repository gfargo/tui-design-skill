**No. Use one scheduler that owns the clock, and let each widget declare how often it needs data.** Only a slow or expensive source should get its own background cadence.

## The premise is off

btop doesn't run the CPU box at 100 ms and processes at 2 s. It has **one refresh rate, `update_ms` (default 2000 ms), shared by every box.** Each box keeps its own scroll position, focus, and graph history. They all sample on the same tick. You can change the rate at runtime, and it applies to everything.

The lesson from btop is to make widgets independent in state and data source, but share the clock when sources are cheap and similar.

## Why one timer per widget causes problems

- **Out-of-phase redraws.** N timers produce N separate repaints per period. That means more terminal writes, more chances of flicker, and more CPU wakeups.
- **Numbers that disagree.** If the CPU box samples at t=0 and the process table at t=0.7 s, total CPU% and the sum of per-process CPU% come from different windows and won't match. Users notice that.
- **Pausing is harder.** Hiding a box, losing terminal focus, or suspending the app all have to reach N timers instead of one.
- **Testing is harder.** One scheduler can be driven with synthetic ticks. Many independent timers can't be tested deterministically.

## Recommended architecture

1. **One scheduler in the event loop.** Each data source registers an interval, e.g. `cpu: base`, `procs: base`, `disk_smart: 30s`. On each tick the scheduler starts whichever sources are due.
2. **Sample off the UI thread.** Collectors run as background tasks and send results back as messages. Never read `/proc`, call `ps`, or hit the network inside update or render.
3. **Keep sampling separate from rendering.** Data arriving marks the affected widgets dirty. Render at most once per frame, and only when something is dirty, a key is pressed, or the terminal is resized. Don't redraw unchanged state.
4. **Don't let slow sources pile up.** If a fetch is still running when the next one is due, skip that tick. Never queue overlapping fetches.
5. **Compute rates from actual elapsed time.** CPU%, network bytes/s, and disk I/O are deltas. Divide by the measured interval, not the nominal one, because ticks drift.
6. **Stop sampling what nobody sees.** Hidden boxes shouldn't sample. If the terminal reports focus changes (mode 1004), pause polling when the window loses focus and refresh right away when it comes back. tmux only forwards these with `focus-events on`.
7. **Expose the rate.** Copy btop: one user-tunable base interval in config, with `+`/`-` to adjust it live. Per-source overrides belong in config only for sources that need them.

```
on tick(now):
  for src in sources where now >= src.next_due and not src.in_flight:
      src.in_flight = true
      spawn(fetch(src)) -> Msg::Data(src.id, sample, elapsed)
on Msg::Data(id, sample, elapsed):
  widgets[id].apply(sample, elapsed); mark_dirty(id)
on frame (if any dirty): render once
```

## When a widget should get its own cadence

Give one its own cadence when its source is **slow or expensive**: SMART disk queries, a remote API, container stats from a daemon, or a full filesystem scan. Even then the shared scheduler still triggers it, just at a longer interval. Don't start a separate timer loop inside the widget.

A sub-second sparkline is a reasonable exception. Here the faster timer is for animation, not for fetching data. Render it from buffered samples on the frame tick, and keep data collection on the shared clock.

If you tell me your stack (Bubble Tea, Ratatui, Textual, or Ink), I can show the native way to do this. Each of them has an idiomatic tick or message pattern that maps directly onto this design.
