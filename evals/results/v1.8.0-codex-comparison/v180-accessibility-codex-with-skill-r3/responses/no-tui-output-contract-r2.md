`--no-tui` should provide a **complete, linear CLI mode**, with the same data and actions as the dashboard. Removing borders still leaves meaning dependent on column positions; a screen reader needs explicit labels and a predictable reading order.

For a dashboard snapshot, output something like:

```text
Dashboard: production
Updated: 2026-10-13 14:32 UTC
Summary: 2 services; 1 healthy; 1 degraded.

Service: api
Status: healthy
Requests per second: 120
Error rate: 0.2 percent

Service: worker
Status: degraded
Queued jobs: 340
Reason: one worker unavailable
Next step: run dashboard inspect worker

Status: snapshot complete.
```

The contract should be:

- **Ordinary terminal output:** retain scrollback and the visible cursor. No alternate screen, raw mode, cursor movement, clearing, spinners, or repainting.
- **Labelled records:** use `Field: value`, full values and explicit units. Express status in words. Replace charts with meaningful summaries; state empty, unavailable, partial, and stale data explicitly.
- **Snapshot by default:** print once and exit. An explicit `--watch` should append timestamped changes at a controlled cadence, without repeating unchanged records.
- **Action parity:** expose every TUI action through subcommands or flags. When interaction is needed, print numbered choices and accept a typed answer. Every prompt needs an unattended equivalent; missing required input must produce an actionable error.
- **Clean streams:** results and final result status on stdout; prompts, progress, warnings, and errors on stderr. Use documented exit codes. Offer `--format json|csv` for automation without adding human commentary to structured stdout.
- **Persistent opt-in:** support the flag plus an environment variable or configuration setting. Automatically use plain mode when stdout is not a terminal; do not depend on detecting a screen reader.

For Ratatui, select this path **before terminal initialization**, sharing the dashboard’s data and action logic with a separate text renderer. Ratatui itself does not supply screen-reader semantics.

At both 80 and 60 columns, the output should remain a single sequence of labelled records with no width-based truncation. Verify redirected output, action parity, error paths, and actual reading order with the screen-reader user.