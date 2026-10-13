`--no-tui` should provide a **complete linear CLI mode**: readable in sequence, preserved in scrollback, with access to every dashboard action. Removing borders leaves users dependent on column positions and remembered headers.

Its contract should be:

- **Label each value.** Replace table rows with record blocks using `Label: value`. Spell out status and units; preserve full values.
- **Append output.** No alternate screen, cursor movement, clearing, redraws, spinners, or animation. Keep the cursor visible.
- **Preserve functionality.** Expose filtering, inspection, refresh, and any dashboard actions through commands and flags. Interactive choices use numbered lists and typed answers; every prompt also has an unattended equivalent.
- **Separate streams.** Results go to stdout. Prompts, occasional progress, warnings, and errors go to stderr. Finish with an explicit status and meaningful exit code.
- **Make it persistent.** Support a flag, environment variable, and saved setting. Automatically use plain mode when stdout is not a terminal; do not rely on screen-reader detection.
- **Offer structured output.** Add `--format json|csv` for automation, without mixing prose into that output.

For example, a service dashboard could print:

```text
Dashboard snapshot
Environment: production
Updated: 2026-10-13 14:32 UTC
Services: 2

Service: api
Status: healthy
Requests per second: 142
Error rate: 0.2 percent

Service: worker
Status: degraded
Queued jobs: 831
Reason: Connection to the database timed out.
Next step: Inspect worker logs.

Status: Snapshot complete. 1 service needs attention.
```

A snapshot-and-exit default is reasonable for a monitoring dashboard. Add an explicit `--watch` option that appends timestamped changes, with a configurable interval, instead of repeatedly printing the whole dashboard.

In Ratatui, branch into this mode **before initializing the terminal UI**, and share the data and action layer between both interfaces. At 80×24 or in a 60-column split, plain output remains one linear sequence: no hidden fields, width-based truncation, or minimum-size screen.

The current borderless output has zero border nesting, but still carries the table’s spatial dependency. Remove alignment padding, decorative row markers, and redundant status symbols; retain field labels because they supply the meaning.

Verify redirected output, absence of terminal control sequences, action parity, and actual use with the reporting user’s screen reader.