The viewer should open in **live follow mode**, with one log event per row. Keep the default view compact; show the full JSON only when requested.

```text
payments · LIVE · 2 warnings · 14:32:08
/ level>=warn                         23 matches
TIME         LEVEL  MESSAGE
14:32:05.218  WARN   Retry scheduled · attempt=2
14:32:06.031  ERROR  Charge failed · code=timeout
14:32:08.442  WARN   Upstream slow · duration=…
                         ↓ 3 new · f to follow
```

The bottom “new” indicator appears only when the user has scrolled away from the live end. Otherwise, the last row shows a brief key hint:

```text
/ filter   Enter details   Space pause   ? help
```

In a narrow pane, drop columns before truncating messages:

```text
payments · LIVE
/ level>=warn
32:05 W Retry scheduled
32:06 E Charge failed
32:08 W Upstream slow…
↓ 3 new · f follow
```

Use `D I W E F` severity letters alongside optional color. Never rely on color alone. Escape control characters from log content so an event cannot move the cursor or change the terminal title.

**Event details**

`Enter` opens details for the selected event, replacing the list in a narrow pane:

```text
Event 4821 · ERROR
timestamp  2026-10-28T14:32:06.031Z
message    Charge failed
service    payments
request_id req_91ab
error.code timeout

j/k scroll · Tab raw JSON · Esc back
```

Messages stay on one row in the list; details wrap long values and preserve multiline content. Preserve the original input bytes for export.

**Key bindings**

| Key | Action |
|---|---|
| `j` / `k`, `↓` / `↑` | Move selection; moving away from the end stops following |
| `PgUp` / `PgDn` | Scroll one page |
| `g` / `G` | Oldest / newest retained event; `G` does not resume follow |
| `f` | Jump to newest and resume following |
| `Space` | Pause/resume viewport updates; ingestion continues |
| `/` | Edit filter; `Enter` applies, `Esc` cancels |
| `n` / `N` | Next / previous text-search match |
| `Enter` | Open selected event |
| `Tab` | Toggle formatted fields / raw JSON in details |
| `Esc` | Close details, help, or the current prompt |
| `?` | Show help |
| `q`, `Ctrl-C` | Exit and restore the terminal |

Keep **filtering and searching distinct**: filters hide events; search highlights and navigates within visible events. Filter input defaults to literal text, with an explicit structured form such as `level>=warn service=payments`. Show syntax errors inline and keep the previous valid filter active. Never execute filter text as shell code.

**Behavior beyond the happy path**

| Situation | Behavior |
|---|---|
| User scrolls while logs arrive | Keep the selected event anchored. Count new matching events below; never snap back automatically. |
| Pause lasts a long time | Continue reading into a bounded buffer. Show retained range and eviction count; pausing does not promise permanent retention. |
| Log volume exceeds capacity | Bound memory by bytes and event count. Batch redraws. Explicitly report any dropped events; never silently discard them. |
| Malformed JSON | Keep the line as an event marked `INVALID JSON`, with a parse error in details. Continue reading. |
| Missing or unfamiliar fields | Show available fields; missing time or level becomes `—`. Support configurable field paths for nested schemas. |
| JSON value is an array or scalar | Display it as valid JSON without assuming it is an object. |
| Partial line at the live end | Wait for newline. At EOF, accept a valid final JSON value; otherwise show an incomplete/invalid record. |
| Huge record | Cap interactive parsing and preview size; show the limit and truncation clearly. Do not present a truncated export as the original record. |
| Out-of-order timestamps | Preserve arrival order. Show supplied timestamps without reordering the stream. |
| Empty input or zero matches | Distinguish “waiting for logs” from “no events match”; show received and matched counts. |
| File rotates or is truncated | Follow by filename by default, reopen replacements, and insert a visible source-change marker. Offer descriptor-follow mode. |
| SSH disconnects or the source fails | Show the error and last-received time. Reconnect only for a source that supports it; mark gaps and reconnect boundaries. |
| Terminal resizes | Reflow columns and details while retaining selection. At extremely small sizes, show a minimal status and latest message. |
| No color or limited terminal | Respect `NO_COLOR`; use severity letters and basic terminal capabilities. Restore cursor and terminal mode on exit. |

**Pipes are a separate, predictable output mode.**

- If stdout is not a TTY, emit JSONL with no UI, ANSI codes, headers, or status messages. Put diagnostics on stderr.
- With no filter or transformation, pass input through unchanged. With filtering, emit original matching records and document how malformed records are treated.
- Never silently drop records in pipe mode: apply backpressure. On a closed downstream pipe, exit quietly.
- When stdin supplies logs, read interactive keys from the controlling terminal. If none exists, use stream mode; an explicit `--interactive` request should fail with a clear explanation.
- Provide `--output=jsonl|text` and `--interactive` so scripts do not depend solely on terminal detection.

The essential contract is that the UI may abbreviate what it displays, but it always makes pauses, gaps, truncation, and lost history visible.