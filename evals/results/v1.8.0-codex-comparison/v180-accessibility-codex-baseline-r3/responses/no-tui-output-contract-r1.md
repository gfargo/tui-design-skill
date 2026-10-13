`--no-tui` should provide a **plain-text interface designed for linear reading**, rather than a borderless version of the visual dashboard.

It should:

- Print one snapshot and exit by default. Offer an explicit `--watch` mode for ongoing updates.
- Use ordinary stdout text: no cursor movement, screen clearing, ANSI styling, spinners, or terminal-size-dependent layout.
- Present information in a meaningful reading order, with explicit labels. Don’t rely on columns, color, icons, or spatial position to convey meaning.
- Spell out statuses and units, and distinguish “unknown” from zero.
- Include the dashboard’s important information and alerts, plus command-line equivalents for essential actions.
- Keep output deterministic and pipeable. Offer `--format json` separately for automation.

For example, instead of a table:

```text
Dashboard snapshot
Updated: October 13, 2026, 10:42 AM EDT

Summary
Services: 3
Healthy: 2
Degraded: 1
Active alerts: 1

Alert
Worker queue exceeds the warning threshold.
Queued jobs: 1,240. Warning threshold: 1,000.

Service: API
Status: Healthy
Requests per second: 842
Error rate: 0.2 percent
95th percentile latency: 120 milliseconds

Service: Worker
Status: Degraded
Queued jobs: 1,240
Oldest queued job: 8 minutes

Service: Scheduler
Status: Healthy
Last successful run: 2 minutes ago
Next scheduled run: 10:45 AM EDT
```

For watch mode, append timestamped changes instead of redrawing the screen. Avoid repeating unchanged data at every refresh.

The acceptance test is straightforward: **can someone understand the state and take essential actions by reading the output sequentially, without seeing its layout?** Validate that with the screen-reader user; removing borders alone doesn’t meet it.