**No.** Also, btop doesn't work the way you describe. It has a single refresh rate, `update_ms` (2000 ms by default), and every box uses it. The CPU box isn't on its own 100 ms timer; you can lower `update_ms` and all boxes update faster together. What each btop box does own is its scroll position, focus, and graph history, not its own clock.

## Recommendation: one clock, with per-widget rates when needed

Start with **one shared tick**. Only give a widget its own rate when its data source is slow or expensive. That's the rule btop follows: cheap, similar sources (`/proc` reads, sysctl) share one clock.

When rates do differ, still don't give each widget its own timer. Use one scheduler where each widget states how often it wants to update:

```
widgets declare:   cpu: 1s   mem: 1s   net: 1s   procs: 2s   disk-smart: 30s
scheduler:         one tick at the shortest rate needed (or a min-heap of next-due times)
on tick:           start collection for widgets that are due → off the UI thread
on result:         update that widget's state → mark it changed
render:            one redraw per batch of changes, not one per widget
```

Separate timers cause problems that this avoids:

- **Redraws out of step.** Five timers mean up to five redraws a second at slightly different moments, which causes flicker. Rendering also costs more than the data collection for most monitors.
- **Wasted work.** You can't easily skip unchanged frames or pause everything at once. With one scheduler, you can stop polling when the terminal loses focus (focus reports, mode 1004) and refresh as soon as it comes back.
- **Hard to test.** One clock you control lets you feed in fake ticks and check each widget's state without a terminal. Many independent timers mean tests that depend on real time and sometimes fail.
- **Overlapping work.** If a slow collection (process table, SMART data, a network call) runs longer than its interval, a separate timer can start a second one on top. A scheduler can skip a widget that's still running instead of piling up work.

## Rules to keep

- **Separate data collection from rendering.** Ticks start collection. Results come back as messages, channels, or tasks. Redraws happen only on input, new data, resize, or a deliberate tick, never in an unconditional loop.
- **Never block the UI thread** on collection. Listing processes is the slowest part, so it's the one most likely to need its own slower rate.
- **Let users change the rate,** as btop does (`update_ms` plus `+`/`-` keys). Show the current interval in a box title or the status bar so people know how fresh the data is.
- **Show stale or failed data honestly.** If one widget's source fails, show it as stale or in an error state inside that widget only. Don't freeze the shared clock, and don't change the saved layout. btop has an open bug where a temporarily missing GPU permanently rewrites the user's saved layout.

Each framework has a standard way to set this up: Bubble Tea's `tea.Tick` commands feeding into `Update`, Ratatui's `select!` over an input channel plus one `interval`, Textual's `set_interval` on the app rather than on each widget, or one hook at the top of an Ink app. Tell me which stack you're using and I'll sketch the scheduler in its style, along with how the layout should behave at 80×24 and in a 60-column tmux split.
