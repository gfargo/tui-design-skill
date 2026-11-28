Build a **single log list with record drill-down**, starting in follow mode. Give it two output contracts: an interactive alternate-screen viewer for terminals, and a plain streaming filter for pipes.

The main loop is: watch → pause → search or filter → inspect a record → resume.

**Screen layout**

Wide, 120+ columns; details appear only after Enter:

```text
api / prod-eu / app.jsonl                         FOLLOW
14:02:11.023 INFO  request complete   | Record 1843
14:02:11.108 WARN  upstream slow      | time: 2026-10-28T14:02:11Z
14:02:12.004 ERROR upstream timeout  | level: error
14:02:12.110 INFO  retry scheduled    | message: upstream timeout
                                    | request_id: a81
                                    | duration_ms: 5000
                                    | upstream: payments
                                    |
filter: level >= warn               | Tab fields/raw
PAUSED  23 new matching  |  8,120 retained
F follow  / search  f filter  Enter details  ? help
```

The selected row uses reverse video. Opening details pauses follow and pins that record. No sidebar, graph, or permanent detail panel.

At **80×24**, the list occupies the full width; Enter replaces it with details. Keep milliseconds, level, and message; omit configurable secondary columns first. Three fixed rows—header, status, shortcuts—leave 21 for data. An active filter uses one additional row.

At **60 columns**, keep the same single-pane structure:

```text
api / prod-eu                           PAUSED
14:02:11 INFO  request complete
14:02:11 WARN  upstream slow
14:02:12 ERROR upstream timeout after 5000...
14:02:12 INFO  retry scheduled

filter: level >= warn
23 new matching | 8,120 retained
F follow  / search  f filter  Enter details  ? help
```

Hide fractional seconds and secondary metadata first; preserve level and message. Details remain full-screen, with wrapped values and vertical scrolling.

Declare **60×8** the minimum. Below it:

```text
Need 60x8; current 48x7.
Resize; q quits; ? help.
```

Continue ingestion with the same bounded retention policy while too small. Resizing preserves selection, filters, and follow state.

**Key bindings**

| Key | Behavior |
|---|---|
| Up/Down, `k`/`j` | Move by record; moving into history pauses follow |
| PgUp/PgDn | Move one page, retaining one row of overlap |
| Home / `g` | Oldest retained record; pause |
| End / `G` | Newest matching record; resume follow |
| `F` | Toggle follow; resuming jumps to the newest match |
| `/` | Literal search across retained, filtered records; Enter commits |
| `n` / `N` | Next/previous match; show position and match count |
| `f` | Edit structured filter, e.g. `level >= warn and request_id = "a81"` |
| Enter | Inspect selected record; pause and pin its contents |
| Tab in details | Switch parsed fields/raw JSON |
| `w` | Toggle wrapping; off by default in the list |
| Left/Right | Scroll overflowing list content horizontally |
| `e` | Export a snapshot of retained matching records to a named file |
| `?` | Contextual help with every binding |
| Esc | Cancel edit/action, close overlay, clear search/filter, or return from details—one step per press; never quit |
| `q` | Back from details/help; quit at the root |
| Ctrl+C | Cancel an explicit operation first; otherwise quit cleanly |
| Ctrl+Z | Suspend with terminal restored; redraw on resume |

Printable shortcuts become ordinary characters inside text fields. Enter applies a filter; an invalid expression leaves the previous filter active and shows the error beside the input. Multiline paste never submits a command.

Search highlights and navigates; **filtering hides records**. Applying a filter preserves follow if already following. Searching pauses. Clearing either does not silently resume.

**Behavior when things get awkward**

| Situation | Defined behavior |
|---|---|
| New logs while reading | Keep the viewport and selected record steady. Show “23 new matching,” separately from total arrivals when filtered. Scrolling back to the bottom alone does not resume. |
| Large volume | Retain, for example, at most 50,000 records **and** 64 MiB. Evict oldest first; show cumulative eviction count. Cap repaint rate and send changed cells to keep SSH responsive. |
| Selected record is evicted | Keep an open detail snapshot, labelled “outside retained history.” In the list, select the nearest surviving record and show “earlier history expired.” |
| Input exceeds processing capacity | Bound queues. Backpressure a pipe; for files, show unread byte lag. Report any source-side loss or deliberate drops explicitly. Retention eviction and unread-data loss are different counters. |
| Malformed JSON | Show a `PARSE` record with source position, escaped original content, and error details. Never silently discard it. |
| Partial line | Hold until newline; show “waiting for complete record” if needed. At finite EOF, process the final unterminated line once. |
| Huge record | Enforce a documented configurable limit, such as 1 MiB. Show an oversized-record diagnostic and drain to the next newline; never exhaust memory. |
| Missing or unusual fields | Configurable timestamp/level/message paths. Missing timestamp displays `--`; unknown severity displays `OTHER`; scalar/array JSON remains inspectable. Preserve original fields. |
| Out-of-order timestamps | Keep arrival order. Show full date and timezone in details; compact list timestamps use a documented timezone. Never reorder a live list automatically. |
| Hostile terminal content | Escape ANSI, OSC, carriage returns, and other controls before rendering. A logged string cannot clear the screen, change the title, or write the clipboard. |
| Unicode and long messages | Measure terminal cells, truncate at grapheme boundaries, and mark overflow. Details reveal full content. ASCII mode requires no special fonts. |
| File rotation/truncation | Follow the filename across replacement, drain the old file before switching, and mark the boundary. Detect truncation and restart at offset zero. Document that copy-truncate races can lose data. |
| Source becomes unavailable | Preserve old rows; show `DISCONNECTED`, last arrival time, retry countdown, and `r retry`. Never label silence alone as disconnection. |
| Empty source / empty filter | Distinguish “Waiting for first record” from “0 matches; 8,120 retained—f edit filter.” |
| EOF | A file in follow mode waits for growth. Finite stdin shows `EOF` and remains browsable in the TUI; streaming mode exits. |
| Export | Capture matching retained records at invocation, in arrival order. Write original complete lines; report count and omissions. No silent overwrite. Live arrivals belong to a later export. |

Start file sessions with the last 1,000 records and follow; offer `--tail N`, `--from-start`, and `--no-follow`. A piped input is consumed from its beginning. Filters operate on retained history and future arrivals, never pretending to search evicted records.

**SSH and pipeline contract**

Using `jlog` as a placeholder command name:

```sh
jlog --follow app.jsonl
ssh host 'tail -F /srv/api/app.jsonl' | jlog -
jlog --follow app.jsonl --where 'level >= warn' | jq .
```

- Auto-enable the TUI when stdout is a capable terminal and a controlling terminal is available. When stdin carries logs, read keys from `/dev/tty`.
- Redirected stdout selects streaming mode automatically: **no escapes, headers, progress, pager, or prompts**. Diagnostics go to stderr.
- Streaming defaults to original JSON-lines bytes. `--format jsonl` validates records and fails on malformed/oversized input; explicit `--invalid=skip` permits skipping with diagnostics. Never inject diagnostic objects into the service’s schema.
- `--no-tui --format text` provides append-only, labelled human output for accessibility and scrollback. Filtering, searching, field selection, and export have CLI equivalents.
- Streaming follows downstream backpressure; it does not apply the TUI history cap. A closed downstream pipe exits promptly without a traceback.
- Exit codes: `0` for completion or `q`, `2` for invalid arguments/filter syntax, `1` for fatal input/output failures, `130` for interruption. No matches is success.
- Use ordinary keys throughout; require no tmux configuration or enhanced keyboard protocol. Mouse capture is off by default.
- Honor `NO_COLOR`, provide ASCII output, and preserve meaning through level labels and explicit state words.
- Restore cursor, raw mode, alternate screen, and enabled input modes on normal exit, error, interrupt, and suspend. Ordinary file ingestion is not treated as an operation that swallows Ctrl+C.

The clutter audit is deliberately strict: **zero enclosing borders**, one separator only when wide details are open, no marker repeated on every row, and at most a level word plus optional color for severity. Remove repeated service names, JSON key labels, and full dates from list rows. At 80×24, fixed chrome consumes 12.5% of rows; the rest belongs to logs.