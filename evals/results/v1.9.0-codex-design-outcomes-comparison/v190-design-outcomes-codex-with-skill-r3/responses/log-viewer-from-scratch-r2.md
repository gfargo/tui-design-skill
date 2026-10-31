Use a full-screen, single-list viewer with an on-demand detail view. The main loop is **follow → notice something → pause → inspect → resume**. Give piped output a separate, stable stream contract.

Call it `jtail` in these examples.

**Screen layout**

One event per row, oldest first. New events arrive at the bottom. Rows never wrap; `...` means more content is available in details.

Wide terminal, with details explicitly opened:

```text
jtail api@prod-2 /var/log/api.jsonl          PAUSED +143 new
filter: level>=warn

  TIME         LEVEL MESSAGE                   | Event #812
  14:22:01.102  WARN  retrying payment           | time: 2026-10-28T14:22:02Z
> 14:22:02.041  ERROR upstream timeout           | level: error
  14:22:03.508  WARN  circuit opened             | message: upstream timeout
                                               | request_id: rq_9f2
                                               | upstream: payments
                                               | duration_ms: 3000
                                               |
                                               | v raw JSON

Enter details  / find  f filter  Space resume  ? help  q quit
```

The `>` represents the selected row; reverse video provides its actual emphasis. The detail pane appears only on request, never automatically.

At **80×24**, the list wins. Details replace the list, and returning restores the selected event and scroll position. Three chrome rows leave 21 event rows: source/status, filter, footer. No separate column-header row.

At **60 columns**, the same design remains usable:

```text
api@prod-2                         PAUSED +143 new
filter: level>=warn
  14:22:01 WARN  retrying payment
> 14:22:02 ERROR upstream timeout
  14:22:03 WARN  circuit opened
  14:22:04 ERROR request failed: upstream ret...
  14:22:05 WARN  retry budget exhausted










Enter detail  / find  f filter  Space live  ? help
```

Responsive rules:

| Size | Behavior |
|---|---|
| ≥120 columns | Optional details beside list; preserve at least 60 columns for logs. |
| 80–119 | Single list; full-screen details. Show milliseconds where space permits. |
| 60–79 | Drop milliseconds and optional metadata columns. Message gets remaining width. |
| 40–59 | Hide timestamps; retain level and message. Shorten source and hints. |
| Below 40 columns or 6 rows | Show `Terminal too small; need 40x6`, current size, and quit/help hints. Continue bounded ingestion. |

Resize preserves selection, filters, and follow state. It never silently resumes scrolling.

**Key bindings**

Bindings apply in browsing mode; letters remain ordinary text inside prompts.

| Key | Action |
|---|---|
| `Up` / `k`, `Down` / `j` | Select previous/next event; leaving the live edge pauses follow. |
| `PgUp` / `PgDn` | Move one viewport; `u` / `d` are plain-key alternatives. |
| `Home` / `g` | Oldest retained event. |
| `End` / `G` | Newest retained event, without changing pause state. |
| `Space` | Pause follow; when paused, jump to newest and resume. |
| `Enter` | Open selected event details. Opening details pauses follow. |
| `v` | In details, toggle formatted fields and escaped raw JSON. |
| `Left` / `h`, `Right` / `l` | Pan clipped content horizontally. |
| `/` | Find literal text in retained, filtered events. |
| `n` / `N` | Next/previous match; announce wrapping. |
| `f` | Edit structured filter, such as `level>=warn request_id="rq_9f2"`. |
| `?` | Contextual help, including filter syntax and buffer limits. |
| `Esc` | Cancel prompt or close help/details; at the main list, clear search highlighting. Never quits. |
| `q` | Close help/details first; quit from the main list. |
| `Ctrl+C` | Cancel an active prompt; otherwise quit immediately. |
| `Ctrl+Z` | Suspend on supported systems; restore terminal before handoff and redraw on resume. |

No action requires function keys, Alt combinations, extended keyboard support, or tmux’s `Ctrl+B`.

Search highlights and navigates; filtering removes rows from view. Search covers the full event, including hidden fields. A hidden-field match opens details at that field. Both operations pause follow. Prompt changes commit with Enter; invalid filters keep the previous filter active, with an error beside the offending expression. Esc restores the previous value. Multiline paste is rejected without submission.

**Follow and retention**

- **Pause freezes the viewport, not collection.** Show `PAUSED +143 new`, counting arrivals since pause, with matching counts available in expanded status.
- Selection uses a stable event identity, never a row index. New arrivals cannot move the event being inspected.
- Retain, for example, the newest **50,000 events or 64 MiB**, whichever limit comes first; make both configurable. State the retained range in help/status.
- Keep one inspected event pinned outside the rolling history. If surrounding history expires, say `Earlier history expired`; never pretend it remains searchable.
- Throttle rendering to about 10 frames/second over SSH. Collection and keyboard handling stay independent of painting.
- When ingestion cannot keep up, expose backlog and apply bounded backpressure. Any unavoidable source loss gets a persistent gap notice with an exact count when known, otherwise `count unknown`. Pipeline mode never silently drops records.

**Pipes and shell behavior**

```sh
jtail --follow /var/log/api.jsonl
ssh prod 'tail -F /var/log/api.jsonl' | jtail -
jtail --follow --filter 'level>=warn' api.jsonl | jq '.request_id'
jtail --no-tui --format=text --follow api.jsonl
```

- Start the TUI only when stdout is a capable terminal and a controlling terminal is available. With piped stdin, read keys from `/dev/tty`, never from the log stream.
- Redirected stdout, `TERM=dumb`, or `--no-tui` selects linear output: no alternate screen, prompts, cursor motion, color, headers, or truncation.
- Default machine output preserves original matching JSON records, one per line; do not rename fields, normalize timestamps, or inject viewer status records. Diagnostics go to stderr.
- `--format=text` provides labeled, escaped, linear human output for accessibility. Filter, search, context, detail, and raw-view operations have CLI equivalents.
- Regular files print their contents and exit unless `--follow` is specified. Following defaults to the last 200 records; `--from-start` reads everything. Stdin streams until EOF.
- Missing source with terminal stdin shows usage instead of waiting for keyboard input as logs.
- Exit codes: `0` normal completion or `q`; `1` source/I/O failure; `2` usage/filter error. No matches is success. SIGINT restores the terminal and preserves signal semantics, conventionally 130. A downstream closed pipe exits silently, conventionally 141.

**The cases that otherwise become surprises**

| Case | Defined behavior |
|---|---|
| Startup/loading | Immediately show source and `Opening...`; keep quit responsive. |
| Quiet service | `Waiting for first event` or `Last received 2m ago`. Silence alone does not mean disconnected. |
| Filter matches nothing | Say `No matching events; 8,412 received`, and offer `f` to edit. |
| EOF | TUI retains history with `EOF`; linear mode exits. A closed SSH input is not automatically reconnected. |
| Read failure/disconnection | Keep retained events visible with the failure reason. Retry retryable file-follow failures with visible backoff; permission failures offer an explicit retry. |
| File rotation/truncation | Follow the named path, drain the old file to observed EOF, then switch. Mark rotation/truncation as viewer notices, separate from service events. Do not promise lossless `copytruncate`. |
| Partial final line | Buffer until newline; at EOF, parse the remaining bytes once. In file-follow mode, wait for completion. Show pending-byte status for a stalled large fragment. |
| Malformed JSON | TUI shows a `PARSE` event with escaped source text and location. Machine mode fails with line number on stderr by default; explicit `--invalid=skip` continues with counted diagnostics. |
| Huge record | Configurable 1 MiB default limit. TUI shows an oversize notice and bounded preview. Machine mode fails unless skipping is explicitly requested. |
| Schema differences | Recognize common time/level/message aliases, with explicit field-path overrides. Missing time becomes `--`; unknown level becomes `?`. Preserve every original field. |
| Out-of-order timestamps | Preserve arrival order. Details show original timestamp, timezone, and receipt time; never reorder a live list unexpectedly. |
| Stack traces, Unicode, hostile text | Expand stack traces in details. Measure terminal cells correctly. Escape embedded control sequences, carriage returns, and bidi controls so logs cannot manipulate the terminal. |
| Clipboard over SSH | Mouse capture is off by default for terminal/tmux selection. No automatic clipboard writes; raw CLI output provides a dependable extraction path. |
| Terminal capability failure | Render immediately with conservative defaults; capability queries have bounded timeouts. Honor `NO_COLOR`, use textual levels, and require no special fonts. |
| Quit, crash, suspend | Restore raw mode, cursor, alternate screen, and enabled input modes. Avoid printing diagnostics into the active TUI. |

The clutter audit is deliberate: **zero nested borders**, no per-row bullets or repeated service names, one selection cue, and at most text plus color for severity. Three chrome rows consume **12.5% of an 80×24 screen**. Remove dashboards, permanent JSON previews, and decorative separators; give those cells to logs.