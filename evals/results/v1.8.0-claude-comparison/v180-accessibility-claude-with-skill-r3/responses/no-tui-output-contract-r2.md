**Short answer:** `--no-tui` should be a separate linear interface, not the dashboard with the borders removed. A borderless table is still a 2D grid. A screen reader reads it row by row, so the listener has to remember which column is which, and the aligned spacing either gets read out or tells them nothing. Ratatui has no screen-reader support (it's an open tracking issue upstream), so this mode is the accessibility answer for your app. Treat it as a real product surface.

## What it should output

Write labelled sentences and `Header: value` blocks. Put the summary first and the worst problems next, and finish with a status line.

```
$ dash --no-tui
prod-east: 2 of 14 services need attention.

Service: billing-worker
Status: down
Down since: 13:48, 14 minutes ago
Last error: connection refused by postgres-primary

Service: api-gateway
Status: degraded
Latency p95: 840 ms, threshold 500 ms
Error rate: 2.1 percent

12 other services are healthy. Run "dash status --all" to list them.
```

Why it's built this way:
- **The count comes first** so the listener knows how much is coming before hearing details.
- **Healthy rows are collapsed by default.** Each one costs listening time, and on a dashboard the problems are what matter.
- **Every value has a label**, so meaning never depends on column position, color, or a ✓/✗ glyph.
- **No box drawing, sparklines, bar charts, or ASCII art.** Screen readers read them as symbol noise. Turn a sparkline into words, like "latency rising for 10 minutes."
- **Units are spelled out** where symbols read badly ("percent," "ms" is fine).

## Live updates: append, don't repaint

A refreshing dashboard is the worst case for screen readers, because every redraw gets announced as new text. Add an opt-in watch mode that prints a line **only when state changes**, with the kind of line first:

```
$ dash --no-tui --watch
Watching prod-east. New events print below. Press Ctrl+C to stop.
warning: 14:02 api-gateway is degraded. p95 latency 840 ms, threshold 500 ms.
error: 14:03 billing-worker is down. Connection refused by postgres-primary.
recovered: 14:09 billing-worker is up.
```

Don't print on every tick and don't use spinners. If a fetch is slow, print one `Fetching metrics…` line to stderr and then the result.

## Every TUI action needs a plain equivalent

The mode has to reach everything the dashboard can do. Otherwise screen-reader users are locked out of features, not just layout.

| TUI interaction | Plain-mode equivalent |
|---|---|
| Select a row, press `r` to restart | `dash restart billing-worker` |
| Confirmation modal | Prompt on stderr: `Restart billing-worker? Type yes to confirm:`, plus `--yes` for unattended runs |
| Arrow-key picker | Numbered list, then read a typed number |
| Filter or sort keys | `--filter status=down`, `--sort latency` |
| Detail pane | `dash show api-gateway` |

## Errors are spoken, labelled, and actionable

```
error: Could not reach the metrics server at metrics.internal:9090.
Check that you are connected to the VPN, then run dash again.
```

Use distinct exit codes: 0 for OK, nonzero for fetch failures, and optionally another code for "services unhealthy" so scripts can branch.

## How it turns on

- `--no-tui` flag, plus an env var (`DASH_PLAIN=1`) and a config key, so the user sets it **once**. gh's `GH_ACCESSIBLE_PROMPTER` is the model. Don't try to detect a screen reader; no tool does this reliably.
- Turn it on automatically when stdout isn't a terminal.
- Keep the stream contract: results on stdout, prompts and progress on stderr. Emit no color.
- Add `--format json|csv` for scripts as a **separate** option. Accessible text is for people and JSON is for machines. Don't make screen-reader users parse JSON, and don't make scripts parse sentences.

## Ratatui implementation notes

Render plain mode from the **data model**, not from the Ratatui widgets. Don't draw to a `Buffer` and strip the borders, which is probably what you're doing now. In plain mode, never call `ratatui::init()`, so there's no alternate screen and no raw mode.

```rust
use std::io::{self, IsTerminal};

let plain = cli.no_tui
    || std::env::var_os("DASH_PLAIN").is_some()
    || config.plain
    || !io::stdout().is_terminal();

if plain {
    return plain::run(&cli, &model); // writes labelled lines; never touches the terminal backend
}
let terminal = ratatui::init();
```

Keep `plain::format_status(&Snapshot) -> String` and `plain::format_event(&Change) -> Option<String>` as pure functions. Golden-test them on healthy, degraded, all-down, empty, and fetch-error snapshots. Add one test that the watch formatter returns `None` for a tick with no changes.

## Next step

Show the reporting user a sample of the output above before building all of it. Ask whether they want healthy services collapsed or listed, and whether timestamps help or get in the way. If you share the dashboard's panels and keybindings, I can map each one to its plain-mode command and output.
