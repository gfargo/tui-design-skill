# Design: `jl`, a terminal viewer for tailing JSON-lines logs

There are three constraints, and each one drives part of the design:

1. **Narrow tmux panes.** The layout changes at fixed widths. It never wraps raw JSON across lines.
2. **Use over SSH.** Every action has a plain key, nothing depends on Esc, the mouse or fancy glyphs, and redraws are throttled.
3. **Use in pipes.** If stdout isn't a terminal, `jl` doesn't draw a UI. It acts as a filter that outputs JSON lines.

---

## 1. Screen layout

### Wide (≥ 100 columns)

```
 api-gateway.log   FOLLOW  ▲ 42/s   12,480 buf   UTC        filter: level>=warn path~charge
─────────────────────────────────────────────────────────────────────────────────────────────
 14:02:11.204 INFO  request done     method=GET path=/v1/users status=200 dur_ms=12
 14:02:11.318 WARN  slow upstream    upstream=billing dur_ms=2304
>14:02:11.540 ERROR request failed   method=POST path=/v1/charge status=502 err="upstream b…
 14:02:12.001 ~     panic: runtime error: index out of range [3] with length 3
 14:02:12.001 ~         goroutine 81 [running]:
 ───────────────────────── 4m 12s gap ─────────────────────────
 14:06:24.990 INFO  service started  version=2.14.1 pid=4411
─────────────────────────────────────────────────────────────────────────────────────────────
 ERROR  2026-10-28T14:02:11.540Z  request failed
   method    POST                    trace_id  4f1c9a0e7b2d4c11
   path      /v1/charge              user_id   u_88213
   status    502                     dur_ms    3012
   err       upstream billing: connection reset by peer
─────────────────────────────────────────────────────────────────────────────────────────────
 /charge  3 of 17                                       ? help  / search  & filter  q quit
```

- **Header line:** source, mode (`FOLLOW` / `PAUSED +214 new` / `EOF`), ingest rate, buffer size, display timezone, and the active filter.
- **Log list:** one entry per row. Columns are time, level, message, then the remaining fields as `k=v`, cut off with `…` at the edge.
- **Detail pane:** opens with `Enter` and shows every field of the selected entry, including pretty-printed nested JSON. It takes up to 40% of the height.
- **Status line:** the search or filter prompt, the match counter, and key hints. Hints drop out as space runs short.
- `~` in the level column marks a line that isn't JSON (see §3).

### Narrow (40–99 columns), e.g. a third of a tmux window

```
api-gw  PAUSED +214   lvl≥W
────────────────────────────────────────
14:02:11 I request done
14:02:11 W slow upstream
14:02:11 E request failed
14:02:12 ~ panic: runtime error: ind…
14:02:12 ~     goroutine 81 [running…
──────── 4m 12s gap ────────
14:06:24 I service started
────────────────────────────────────────
/charge 3/17                     ? help
```

- Milliseconds and the date are dropped. Level becomes a single letter (`T D I W E F`) and color is never the only signal.
- Fields are hidden, so each entry takes one row and stays easy to scan. Press `x` to show them indented on a second row.
- `Enter` opens details **full-screen** instead of in a split, with fields stacked one per line:

```
ERROR  14:02:11.540Z
request failed
────────────────────────────────────────
method    POST
path      /v1/charge
status    502
err       upstream billing: connection
          reset by peer
trace_id  4f1c9a0e7b2d4c11
────────────────────────────────────────
q back  y copy  n/p next/prev entry
```

### Tiny (< 40 columns or < 8 rows)

The header is removed and the header and status lines merge into one. Time shows as `MM:SS`. If the terminal is smaller than 20×4, `jl` shows only `jl: pane too small (18x3)` and keeps ingesting until the pane is resized.

The layout recalculates on every `SIGWINCH`. The selected entry stays at the same position on screen, so a resize doesn't move the cursor.

---

## 2. Key bindings

The choices follow a few rules:

- Movement keys match `less`/vim.
- No Ctrl-a or Ctrl-b, which are tmux and screen prefixes.
- Nothing requires Esc: tmux's `escape-time` makes Esc feel laggy over SSH, so `q` also closes any panel.
- No chord takes more than two keys.

| Key | Action |
|---|---|
| `j` / `k`, `↓` / `↑` | Move the selection |
| `d` / `u`, `PgDn` / `PgUp` | Move half a page / a full page |
| `g` / `G` | Go to the oldest entry in the buffer / the newest. **`G` also resumes follow.** |
| `f` or `Space` | Toggle follow/pause. Scrolling up pauses automatically. |
| `Enter` | Open or close the detail view of the selected entry |
| `n` / `p` (in detail) | Show the next or previous entry's details |
| `/` `?`… | Search forward. `?` on an empty list shows help; `N` searches backward. |
| `n` / `N` | Jump to the next or previous match |
| `&` | Filter, which hides non-matching entries (same as `less`). An empty `&` clears it. |
| `1`–`6` | Minimum level: 1=trace … 4=warn, 5=error, 6=fatal. `0` shows all levels. |
| `x` | Show or hide fields in narrow mode |
| `w` | Toggle wrapping of long lines (off by default) |
| `h` / `l`, `←` / `→` | Scroll horizontally when wrapping is off |
| `t` | Cycle the time display: UTC → local → relative (`-3.2s`) |
| `=` | Show only entries with the same value as the field under the cursor (in detail: `trace_id`, for example) |
| `y` | Copy the selected entry's raw JSON to the clipboard via OSC 52 (§3) |
| `s` | Save the current filtered view as JSONL. Prompts for a path. |
| `\|` | Pipe the filtered view to a shell command, e.g. `\| jq .err \| sort \| uniq -c` |
| `c` | Choose columns, i.e. which fields appear inline and in what order |
| `M` | Toggle mouse support (off by default, see §3) |
| `Ctrl-L` | Redraw the screen |
| `q` | Close the open panel or prompt. With nothing open, quit. |
| `Ctrl-C` | Cancel a prompt. With no prompt open, quit. |

**Filter and search syntax** (the same for `/`, `&`, and `--filter`):

```
error                 free text; matches msg and the raw line
status=502            exact field match
status=5*             glob
path~^/v1/char        regex
dur_ms>1000           numeric comparison
level>=warn           level ordering
-path=/healthz        negation
user.id=u_88213       nested field (dotted path)
a b                   AND; use "a OR b" for OR
```

Filters apply retroactively to everything in the buffer, not just new lines.

---

## 3. Cases you might not have planned for

### Piping and how `jl` is invoked

| Situation | Behavior |
|---|---|
| **stdout isn't a TTY** (`jl app.log \| grep …`) | No UI. `jl` streams **raw JSON lines unchanged** that pass `--filter` / `--level`, so `jq` still works downstream. `--format=text` gives the readable one-line render without color. Output is flushed per line. |
| **stdin is a pipe and stdout is a TTY** (`kubectl logs -f x \| jl`) | Full UI. Keystrokes are read from `/dev/tty`, not stdin. |
| **stdin is a pipe, stdout is a pipe** | Filter mode (see the first row) |
| **There's no `/dev/tty`** (cron, CI) | Falls back to filter mode with a warning on stderr |
| **The downstream reader exits** (`\| head`) | Exits silently with status 0 on SIGPIPE/EPIPE. No stack trace. |
| `TERM=dumb`, or no terminfo entry | Filter mode with `--format=text` |
| `NO_COLOR` is set, or `--color=never` | Level letters and bold stand in for color. Color is never the only signal anywhere. |
| Exit codes | 0 normal, 1 source error, 2 usage error. With `--fail-on=error`, exits 3 if a matching entry was seen, which is useful in scripts. |

### SSH and tmux

- **Redraw throttling:** The screen redraws at most 20 times per second, and only changed rows are sent. At 5,000 lines/s, ingest keeps going while the screen shows the newest state, so the SSH link isn't flooded.
- **Glyphs:** Box-drawing characters and `▲ ≥ …` are used only when the locale is UTF-8. Otherwise `jl` falls back to ASCII (`- > ...`). `--ascii` forces the ASCII set.
- **Colors:** The base 16-color palette by default, so tmux and old terminals don't distort the look. True color is used only if `COLORTERM=truecolor`.
- **Mouse is off by default:** Mouse capture breaks tmux copy-mode and terminal selection, which is how most people copy text over SSH.
- **Copying with `y`:** Sends OSC 52, which reaches the local clipboard through SSH. tmux needs `set-clipboard on`. If `jl` can't confirm the copy worked, the status line says `copied (if your terminal supports OSC 52) — or use s to save`.
- **Alternate screen:** `jl` uses it and restores the terminal on exit, panic, SIGTERM, and SIGHUP (a dropped SSH session). `--no-alt` keeps the last screen visible in the scrollback after quitting.
- **Ctrl-Z:** The terminal is restored before suspending and redrawn on `fg`. Ingest from a file catches up on resume. With stdin, the writer blocks, which is normal pipe backpressure.

### What's in the logs

| Situation | Behavior |
|---|---|
| **Non-JSON lines** (panics, startup banners, stack traces) | Shown with `~` as the level. The time is the arrival time, dimmed. They stay **attached to the preceding JSON entry**, so a filter that matches the entry also shows its stack trace. `--json-only` hides them. |
| **Different field names** | Detected from the first 200 lines: `ts/time/timestamp/@timestamp`, `level/lvl/severity/log.level`, `msg/message/event`. Numeric levels (pino/bunyan 10–60) and syslog levels are recognized. The detected mapping is shown under `?`. Override it with `--ts-field=…` etc. |
| **No timestamp or no level field** | Arrival time is used (dimmed to show it's synthesized), and the level shows as blank `·`. |
| **Epoch timestamps** | Seconds, milliseconds, microseconds, and nanoseconds are told apart by magnitude |
| **Timestamps out of order** | Entries keep **arrival order**; `jl` never re-sorts. A timestamp that goes backwards gets a small `↶` marker. |
| **Time gaps** | A `── 4m 12s gap ──` divider appears where consecutive entries are more than 60 s apart (`--gap=`). This makes restarts and outages easy to spot. |
| **Very long lines** (a 2 MB payload) | Truncated in the list. The detail view shows the first 64 KB of each field with `[+1.9 MB, s to save]`. Lines over 16 MB are kept as a truncated stub so memory can't run away. |
| **Partial line at EOF** | Held until the newline arrives. It's flushed after 1 s of quiet or at EOF, so a crash mid-write is still visible. |
| **Invalid UTF-8** | Shown as `\xNN`. The line still parses where possible. |
| **Wide and combining characters** (CJK, emoji) | Column widths are measured in display cells, not bytes, so truncation never splits a character. |
| **Escape sequences inside log content** | **Removed and shown as visible text** (`\e[31m`, `\x07`). Logs often contain user-controlled input, so a raw OSC sequence could change your terminal title or **write to your clipboard**. This is a real security issue, not cosmetic. `--ansi` allows SGR color codes only, and only when explicitly enabled. |
| Duplicate floods (the same error 10,000 times) | `U` collapses consecutive identical messages into `… ×9,812`. It's off by default so counts aren't hidden unexpectedly. |

### Sources

| Situation | Behavior |
|---|---|
| **Startup on a 40 GB file** | Seeks to the end and loads the last 1,000 lines (`-n`). The whole file is never parsed. |
| **Log rotation** (rename + new file) | Follows the **file name**, like `tail -F`. Shows a `── rotated ──` divider and continues with the new file. |
| **Truncation** (`copytruncate`) | Detected when the size shrinks. Shows `── truncated ──` and reads from offset 0. |
| **File deleted, not recreated** | Header shows `waiting for app.log…`. Everything already loaded stays browsable. |
| **No permission or file missing at start** | Exits with a clear error. `--wait` makes it wait for the file to appear instead. |
| **stdin hits EOF** | Header shows `EOF`. The UI stays open for browsing. `q` quits. |
| **Several files** (`jl a.log b.log`) | Merged in **arrival order** with a short source column (`a│`, `b│`). Sorting by timestamp would delay output and hide clock skew. |

### Buffer and memory

- **Bounded ring buffer:** 50,000 entries or 256 MB, whichever comes first (`--buffer=`). The header shows the current count.
- **Eviction while paused:** If the entries on screen are dropped while you're reading, the view stays put. The top row becomes `── 1,204 older entries dropped (buffer full) ──` so it's clear they're gone. The view never jumps.
- **Search and filter scope:** They cover the buffer only, and the status line says so: `no match in 50,000 buffered`. For a file source, `L` loads older content from disk. For stdin, older content is gone, and the message says that too.
- **Paused counter:** While paused, new entries are counted (`PAUSED +214`), and the count follows the active filter, so it shows only entries you'd actually see. `G` jumps to the newest entry and resumes follow.

### Other behavior

- If the first 200 lines contain no JSON at all, the status line warns: `no JSON detected — showing as plain text`. It still works as a plain pager.
- `?` (help) shows the key list and also the detected field mapping, source path and inode, buffer limits, and terminal capabilities (UTF-8, color depth, OSC 52). Those are what you need when someone says "it looks wrong over SSH."
- `jl --version` and `--help` work without a TTY.
- No config file is required. If `~/.config/jl/config.toml` exists, it sets defaults for field names, columns, and gap threshold. Command-line flags always override it.
