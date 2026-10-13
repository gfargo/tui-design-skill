`--no-tui` should provide a **complete linear CLI**, with the dashboard’s information and actions available in a form a screen reader can follow. Removing borders leaves column relationships implicit and doesn’t provide an accessible workflow.

Its contract should be:

- **Ordinary, append-only text:** preserve scrollback; no alternate screen, raw mode, cursor movement, redraws, spinners, or animation.
- **Labelled records:** replace tables with `Field: value` lines. Include full values, units, textual statuses, and explicit empty, stale, partial, or error states.
- **Action parity:** expose every dashboard action through subcommands or flags. For interactive choices, print numbered options and accept a typed answer. Every prompt needs an unattended equivalent.
- **Clear streams:** results to stdout; prompts, progress, and diagnostics to stderr. End commands with an explicit completion status and return meaningful exit codes. Keep human status messages out of CSV/JSON output.
- **Persistent access:** support the flag plus an environment variable or saved setting; automatically use linear output when stdout isn’t a terminal. Don’t depend on screen-reader detection.

For example, `dashboard --no-tui` could print:

```text
Dashboard snapshot
Updated: October 13, 2026, 10:32 AM Eastern
Services: 2. Healthy: 1. Degraded: 1.

Service: api
Status: healthy
Requests per second: 142
Error rate: 0.2 percent

Service: worker
Status: degraded
Queued jobs: 318
Reason: Cannot connect to the database
Next step: Run dashboard logs --service worker

Status: Snapshot complete.
```

A snapshot-and-exit default is reasonable. Offer explicit `--watch` for monitoring: append timestamped, labelled changes at a controlled cadence instead of repeatedly printing the entire dashboard.

In Ratatui, select this path **before initializing the terminal UI**, sharing data and action logic with the TUI. At both 80 and 60 columns, preserve all fields and let text wrap naturally. Remove alignment padding, borders, row markers, and repeated visual chrome; retain field labels because they convey meaning.

Verify with an actual screen-reader user that they can inspect records, perform actions, understand failures, and recognize completion. A borderless screenshot cannot establish that.