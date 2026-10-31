Build it around **live tailing, readable summaries, and access to the original JSON**. Keep the default screen useful at 40 columns; put richer details in an expandable view.

### Screen layout

At 80 columns:

```text
orders-api  /var/log/orders.jsonl
LIVE  level>=info  /timeout                         3 new errors
TIME          LEVEL  MESSAGE
14:32:08.103   INFO   Listening on :8080
14:32:09.421   WARN   Upstream response slow
14:32:10.017   ERROR  Payment request timed out
14:32:10.026   INFO   Retrying payment request
▸14:32:10.251  ERROR  Payment request timed out
────────────────────────────────────────────────────────────────
14:32:10.251 ERROR  Payment request timed out
request_id  req_8a2f
service     orders-api
duration_ms 3000
upstream    payments
context     {…}  [Enter to expand]
────────────────────────────────────────────────────────────────
LIVE • 1,284 retained • 23 filtered out          / search  ? help
```

At 40 columns:

```text
orders-api
LIVE  >=info  /timeout
14:32:09 W Upstream response slow
14:32:10 E Payment request timed out
14:32:10 I Retrying payment request
▸14:32:10 E Payment request timed out
────────────────────────────────────────
LIVE • 1,284 retained          ? help
```

Design rules:

- One event per row by default. Clip long messages with `…`; expand the selected event to read everything.
- Hide optional columns as space shrinks: context fields first, then milliseconds. Keep severity visible.
- Open details only on request. On short screens, details replace the list instead of squeezing it.
- Use severity letters and text alongside color. Support monochrome and `NO_COLOR`.
- Reserve the bottom row for status, prompts, and actionable errors. Avoid pop-ups during tailing.

### Key bindings

| Key | Action |
|---|---|
| `↑` / `k`, `↓` / `j` | Move selection; moving away from the newest event stops following |
| `PgUp`, `PgDn` | Scroll one page |
| `g` | Go to oldest retained event |
| `G` | Go to newest event and resume following |
| `Space` | Toggle following; ingestion continues |
| `Enter` | Open or close event details; expand a selected nested field |
| `Tab` | Switch focus between list and details |
| `←`, `→` | Scroll clipped content in details |
| `/` | Search retained events |
| `n`, `N` | Next or previous search match |
| `f` | Edit filters |
| `Esc` | Cancel a prompt or close details |
| `?` | Show help |
| `q`, `Ctrl-C` | Exit and restore the terminal |

Label stopped following as `PAUSED • 142 new`; never imply that log ingestion has stopped. `G` is always the way back to live.

### Search, filters, and fields

Keep search and filtering separate:

- **Search** highlights literal text and navigates matches without hiding context. Regex is an explicit option.
- **Filters** hide events, with a persistent summary such as `level>=warn service=payments`. Use a small documented syntax for field equality, severity thresholds, and message text.
- Search and filter the retained buffer, then apply the same rules to incoming events. Display `Search covers retained events` so users do not mistake this for a full-file search.
- Choose conventional fields automatically: `timestamp` / `time` / `ts`, `level` / `severity`, and `message` / `msg`. Allow CLI overrides. Missing fields remain blank; missing messages get a compact JSON summary.
- Preserve input order. Timestamps may be missing, inconsistent, or out of order; do not silently sort them.

### SSH, tmux, and pipes

Make interactive behavior depend on **stdout being a terminal**, with an explicit override.

```text
logview /var/log/orders.jsonl
ssh host 'journalctl -f -o json' | logview
logview --follow service.jsonl --level warn | jq '.request_id'
```

When stdout is a pipe or file:

- Emit JSON-lines only: no screen layout, ANSI escapes, headers, or status messages.
- Preserve each matching record’s original content; send diagnostics to stderr.
- Continue following only when requested with `--follow`. Finite input otherwise finishes at EOF.
- Treat a downstream closed pipe as a normal termination, without a stack trace.
- Apply backpressure rather than silently dropping records.

For piped stdin with an interactive screen, read keys from the controlling terminal. If none exists, use streaming mode. Provide `--interactive` and `--no-interactive` for unusual SSH setups; fail clearly if forced interactive mode cannot access a terminal.

### Cases worth deciding up front

| Case | Behavior |
|---|---|
| User pauses for a long time | Keep a bounded buffer. Show new-event and eviction counts; explicitly report if the selected event was evicted. |
| Logs arrive faster than the screen can draw | Batch redraws and keep memory bounded. Count any lost events; never hide loss. |
| File is renamed during rotation | Finish reading the old file, then follow the replacement at the original path. Show a rotation marker in the UI. |
| File is truncated or temporarily absent | Detect truncation and restart at the beginning. Retry missing paths with visible status and bounded retry frequency. |
| Writer has emitted half a JSON line | Wait for the newline while following. At final EOF, accept a valid unterminated record or report an incomplete one. |
| Malformed JSON or non-object JSON | Show a marked event with the raw content and parse error. Do not crash. In pipe mode, preserve it by default; offer explicit strict/drop-invalid modes. |
| Huge records | Bound parsing and display work with a documented size limit. Show an oversized-record marker; never emit truncated JSON as a valid record. |
| Embedded escapes or control characters | Render them safely. Log content must not execute terminal control sequences or alter the terminal title. |
| Terminal resizes | Reflow immediately while preserving selection and follow state. Below a practical minimum, show a compact resize message while ingestion continues. |
| Nothing matches | Show `No matching events`, the active filters, and a clear way to edit them. Distinguish this from waiting for input. |
| Input ends | Keep the interactive buffer open for inspection and label it `EOF`. Streaming mode exits. |
| Source read fails | Retain already loaded events, show the error, and return a nonzero exit status on exit. |
| Exit or disconnection | Restore cursor, terminal modes, and alternate screen on normal exit and catchable termination signals. |

Two defaults deserve explicit documentation: start file tailing with the **last 100 records**, and retain a buffer bounded by **both event count and bytes**. Show those limits in help, with CLI options to change them.