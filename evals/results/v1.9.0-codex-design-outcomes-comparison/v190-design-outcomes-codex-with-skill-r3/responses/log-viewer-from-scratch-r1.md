Use a **single log list with a full-screen record detail view**. Open in follow mode; scrolling back freezes the viewport while ingestion continues. Keep `FOLLOW` or `PAUSED` visible at every size.

The main loop is: watch → pause → search/filter → inspect → resume.

**Screen layout**

Wide terminal, 120 columns; blank space represents more log rows:

```text
api@prod-3 /var/log/api.jsonl                                      CONNECTED  FOLLOW
filter: level>=warn                                      428 matching / 12,410 kept

  14:32:08.102 WARN  request slow             request_id=ab12 duration_ms=1820
> 14:32:09.447 ERROR upstream timeout         request_id=ab13 upstream=payments
  14:32:09.451 WARN  retry scheduled          request_id=ab13 attempt=2


Space pause  / search  f filter  Enter detail  G follow  ? help  q quit
```

The `>` denotes selection in the sketch; use reverse video in the interface.

At **80×24**, keep timestamp, level, and message. Drop extra fields from rows; show them in detail. At **60 columns**, use the same single-pane layout:

```text
api@prod-3                         CONNECTED PAUSED
filter: level>=warn                    37 new match
  14:32:08 WARN  request slow
> 14:32:09 ERROR upstream timeout
  14:32:09 WARN  retry scheduled


G follow  / search  f filter  Enter detail  ? help
```

Messages truncate with `...`; they never silently wrap into another record. `w` enables wrapping explicitly.

`Enter` replaces the list with details at every width:

```text
api@prod-3 > record 12408                    PAUSED
time        2026-10-28T14:32:09.447Z
level       ERROR
message     upstream timeout
request_id  ab13
upstream    payments
duration_ms 5000

Esc back  r raw/pretty  / search  e export  ? help
```

Details scroll vertically and retain the selected record as new logs arrive. Raw view preserves the original line; pretty view formats JSON.

Below **60 columns**, hide timestamp and counts before sacrificing the message. Support a compact layout down to **40×8**:

```text
api@prod-3 PAUSED +37
ERROR upstream timeout
WARN  retry scheduled



G follow  Enter detail
? help  q quit
```

Below 40×8, show `Too small: need 40x8; q quits`. Keep ingestion running and restore the previous view on resize.

**Key bindings**

| Key | Action |
|---|---|
| `Up/Down`, `k/j` | Move selection; leaving the live end pauses following |
| `PgUp/PgDn` | Move one screen; printable alternatives `b` / Space while paused |
| `g` / Home | Oldest retained matching record; pause |
| `G` / End | Newest matching record; resume following |
| Space | Pause while following; page down while paused |
| `F` | Toggle follow explicitly |
| `/`, `n`, `N` | Search; next/previous match within filtered, retained records |
| `f` | Edit filter; e.g. `level>=warn request_id="ab13"` |
| `Enter` | Inspect selected record; pause |
| `Esc` | Cancel prompt or return from detail/help; no action at root |
| `w` | Toggle wrapping |
| `Left/Right`, `h/l` | Scroll horizontally when unwrapped |
| `e` | Export selected record or a snapshot of retained filtered records to a named file |
| `?` | Scrollable, contextual help |
| `q` | Back from detail/help; quit at root |
| `Ctrl+C` | Cancel active input; otherwise exit with 130 |
| `Ctrl+Z` | Suspend cleanly on supported systems; redraw and refresh source status on resume |

Inside text fields, printable keys—including `q`, Space, and `j`—enter text. Enter applies; Esc restores the previous query. Multiline paste is rejected with an explanation and never submits automatically.

Search highlights and navigates; filtering hides records. Search navigation pauses. Applying a filter preserves follow mode if it was active. Invalid filters retain the previous valid filter and show the error beside the input. Search and filter scope always says **retained records**, so users do not mistake them for a historical server query.

**Pipes and terminal behavior**

Call the tool `jtail` for these examples:

```sh
jtail --follow /var/log/api.jsonl
ssh prod 'tail -F /var/log/api.jsonl' | jtail -
jtail --follow /var/log/api.jsonl | jq 'select(.level == "error")'
jtail --no-tui --output=text --follow /var/log/api.jsonl
```

- Auto-enable the alternate-screen TUI when stdout is a capable terminal and a controlling terminal is available. With piped input, read logs from stdin and keys from `/dev/tty`.
- When stdout is redirected, emit original matching lines without viewer-added ANSI, headers, prompts, or summaries. Diagnostics go to stderr. Do not open a hidden interactive session.
- `--output=jsonl` guarantees valid JSON output; malformed input is a reported error unless an explicit skip policy is selected. Default raw output preserves malformed lines.
- `--no-tui --output=text` provides a linear, sanitized, screen-reader-friendly stream. `TERM=dumb` selects plain mode.
- Plain mode applies downstream backpressure rather than silently dropping output. A closed downstream pipe terminates promptly without a traceback.
- Normal completion and `q` return 0; operational failure 1; argument/filter syntax errors 2; interrupt 130.
- No mouse capture by default, preserving terminal/tmux selection. No essential Ctrl/Alt combinations, clipboard protocol, special fonts, or enhanced keyboard support.

**Cases that need explicit behavior**

| Case | Behavior |
|---|---|
| Starting or waiting for the first record | Show `Opening...`, then `Connected; waiting for records`. Never imply that waiting is an error. |
| Filter matches nothing | Show `No matching records; input still arriving`, total input count, and `f edit filter`. Distinguish this from an empty source. |
| User pauses during a burst | Freeze viewport and selection by record ID. Count new matching records separately from total arrivals. Only `G`, End, or `F` resumes follow. |
| Memory fills | Bound retention by both records and bytes, initially 50,000 records / 64 MiB. Report evicted history. If the selected record expires, keep an open detail snapshot; otherwise show `Selected record expired` before moving to the oldest retained record. |
| Input outruns processing | Batch rendering, keep keyboard input responsive, and use bounded queues. Backpressure where possible; report any unavoidable source loss as a gap. Offer explicit full-stream recording to a file, with disk failures surfaced immediately. |
| File rotates or truncates | `--follow` follows the filename, drains the old file, then reopens its replacement. Report rotation/truncation as viewer status, never fabricate a JSON log record. |
| Source ends or disconnects | Stdin EOF becomes `SOURCE ENDED`; keep retained logs browsable. A failed source becomes `DISCONNECTED` with its reason. Retry only resumable sources; show retry delay and any uncertain gap/duplicate boundary. |
| Quiet service | Show `last record 4m ago`; silence alone does not mean disconnection. |
| Partial final line | Buffer until newline. At final EOF, accept a valid unterminated JSON value; label an invalid fragment as incomplete. |
| Malformed JSON or unexpected schema | Retain and label `PARSE`; expose raw text. Missing fields display `-`; unknown levels remain visible. Allow explicit timestamp/level/message field mappings. |
| Huge records or deep JSON | Enforce documented byte/depth limits; show size and truncation explicitly. Never present truncated data as complete or export it silently as an original record. |
| Clock skew or duplicate timestamps | Preserve arrival order. Display source timestamps with timezone available in detail; do not reorder the live list by time. |
| Escape sequences or hostile text | Render terminal controls visibly, including OSC, ANSI escapes, and bidi controls. Log content must never execute terminal commands. Preserve originals only in explicit raw output/export. |
| SSH latency and resize | Send changed cells, coalesce bursts, and cap redraws around 10 fps. Capability queries have short timeouts and never block first paint. Measure terminal cells for CJK, combining marks, and emoji. |
| Exit, error, or suspend | Restore cursor, raw mode, alternate screen, and every enabled input mode. Resume with a full redraw and refreshed source state. |

Honor `NO_COLOR`; use level text and explicit state labels in monochrome. Color can reinforce severity, but selection needs only reverse video.

The clutter budget is **zero nested borders**, no repeated service name on rows, no per-row status icons, and one severity label plus optional color. Reserve three rows for source/state, filter/counts, and contextual keys: **12.5% of an 80×24 screen**. Keep paths, extra fields, and secondary counters out of narrow rows so messages retain the space.