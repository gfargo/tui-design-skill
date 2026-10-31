# Terminal log viewer for JSON-lines logs

I've used `tailj` as a placeholder name. I'd build it in Go so you can copy one static binary to any box you SSH into.

## The core decision

`tailj` works as two products in one binary, and it picks between them by checking whether stdout is a terminal.

| stdin | stdout | Behaviour |
|---|---|---|
| file argument or terminal | terminal | Full-screen viewer on the alternate screen, following new lines by default |
| pipe (`kubectl logs -f \| tailj`) | terminal | Same viewer. Keys are read from `/dev/tty` because stdin carries the logs |
| anything | pipe or file | **Filter mode, with no UI.** Matching lines go to stdout byte-for-byte as NDJSON, flushed after each line. It follows only with `-f`, like `tail` and `grep`, so scripts still finish |
| anything | terminal with `--plain` | Linear, readable lines with no repainting. This is for screen readers and `script` logs |
| anything | pipe with `--pick` | The viewer is drawn on `/dev/tty`. Lines you mark with `Space` go to stdout when you quit, fzf-style |

The same filter language works everywhere: `tailj app.log --level warn '& req_id=7f3c'` in a script does exactly what `&` does in the viewer.

## Layout

There's no border anywhere. The screen is one header row, the log, and one footer row. Logs need width, so any split stacks vertically, never side by side.

**Wide (120 columns), following:**
```
app.log · UTC · 2026-10-28                                                           FOLLOW · 1.2k/s · 48,213 lines
12:04:01.112 INFO  request completed  method=GET path=/v1/orders status=200 dur_ms=41 req_id=7f3a9c2e user=u_1842 regio…
12:04:01.140 WARN  upstream slow  upstream=inventory dur_ms=1840 attempt=1 req_id=7f3b11d0
12:04:01.203 ERROR upstream timeout  upstream=inventory dur_ms=5000 attempt=3 req_id=7f3c02aa err="context deadline exc…
             raw   panic: runtime error: index out of range [3] with length 3
                     goroutine 81 [running]:
                     main.(*Router).dispatch(0xc0001a2000, {0x9c1e40, 0xc00041e1b0})
12:04:01.377 INFO  request completed  method=POST path=/v1/orders status=201 dur_ms=88 req_id=7f3d5e01 user=u_0093
/ search ⋅ & filter ⋅ L level ⋅ enter detail ⋅ y copy ⋅ F follow ⋅ w wrap ⋅ t time ⋅ ? help
```

**Standard (80×24), paused, with a filter on:**
```
app.log · UTC · & upstream · ≥warn          PAUSED ▾ 37 new · 214/48,213
12:03:58 WARN  upstream slow  upstream=inventory dur_ms=1210 attempt=1 req_id=7…
12:04:01 WARN  upstream slow  upstream=inventory dur_ms=1840 attempt=1 req_id=7…
12:04:01 ERROR upstream timeout  upstream=inventory dur_ms=5000 attempt=3 req_i…
⋮
G follow ⋅ / search ⋅ & filter ⋅ L level ⋅ enter detail ⋅ y copy ⋅ ? help
```
- While following there's no cursor; it behaves like `tail`.
- The first upward key pauses the view and puts a reverse-video cursor on the bottom row.
- The header always says `FOLLOW`, `PAUSED ▾ N new`, or `ENDED`.

**Narrow (60 columns, a tmux split):**
```
app.log · UTC                      FOLLOW · 48,213 lines
12:04:01 INF request completed  method=GET path=/v1/order…
12:04:01 WRN upstream slow  upstream=inventory dur_ms=1840…
12:04:01 ERR upstream timeout  upstream=inventory dur_ms=50…
         raw panic: runtime error: index out of range [3] w…
               goroutine 81 [running]:
/ search ⋅ & filter ⋅ L level ⋅ enter detail ⋅ ? help
```

**Minimum (40 columns):**
```
app.log              FOLLOW · 48,213
INF request completed  method=GET pa…
WRN upstream slow  upstream=inventor…
ERR upstream timeout  upstream=inven…
? help ⋅ / search ⋅ & filter
```

**Detail view (`Enter`).** Below 30 rows it replaces the list. At 30 rows or more it opens as a bottom pane.
```
ERROR · 12:04:01.203 · line 48,190 of 48,213
  "ts":      "2026-10-28T12:04:01.203Z"
  "level":   "error"
  "msg":     "upstream timeout"
  "upstream":"inventory"
  "dur_ms":  5000
▌ "req_id":  "7f3c02aa-91e4-4c1b-a0d2-5d9e1b77c3f0"
  "err":     "context deadline exceeded (Client.Timeout
              exceeded while awaiting headers)"
= filter to this ⋅ ! exclude ⋅ [ ] prev/next ⋅ y copy ⋅ esc back
```
The detail view wraps long values, because it's for reading. The list never wraps by default.

**What gives way as the terminal narrows:**

| Width | What changes |
|---|---|
| Under 100 columns | Milliseconds drop out of the time column (they're still in the detail view) |
| Under 80 | Levels shorten to `ERR`, `WRN`, `INF`, `DBG`. The rate leaves the header |
| Under 60 | The time column goes. The header keeps only the state and the count. The filter text gets cut before the state does |
| Under 40×8 | `tailj: need 40×8, have 32×6 · q quit` appears. `q` and `Ctrl+C` still work |

Extra fields always run inline after the message and are cut off at the right edge with `…`. `Enter` shows all of them.

**How busy it is:**
- **Borders:** none.
- **Level:** shown two ways, the word and its color. `raw` is the only marker, and only the first line of a run of non-JSON lines gets it.
- **Date:** the full date isn't repeated on every row. It sits in the header, and a `── 2026-10-29 ──` separator marks a day change.
- **Selection:** reverse video only.
- **Space spent on chrome:** 2 of 24 rows.

## Key bindings

| Key | Action |
|---|---|
| `j` `k` `↑` `↓`, `Ctrl+D` `Ctrl+U`, `PgUp` `PgDn` | Move. Any upward move pauses following |
| `g` / `G` | Jump to the top. `G` jumps to the bottom and starts following again |
| `F` | Toggle follow, as in `less` |
| `h` `l` `←` `→` | Scroll sideways when wrap is off |
| `/` then `n` / `N` | Search and highlight matches, e.g. `(3/41)`. `Esc` goes back to where you were |
| `&` | Filter the view (`less` uses the same key) |
| `L` | Cycle the minimum level: all → debug → info → warn → error |
| `Enter` | Open the detail view. In it, `=` adds `key=value` to the filter, `!` excludes it, and `[` `]` step to the previous or next log line |
| `Space` | Mark a line (used by `--pick`, `y`, and `s`) |
| `y` / `Y` | Copy the raw JSON line / copy only the message |
| `s` | Save the current filtered lines (raw bytes) to a file. It asks for a path |
| `w` | Toggle wrap |
| `t` | Cycle the time display: absolute → time since the previous line → local time zone |
| `?` | Full help, grouped by area |
| `Esc` | Undoes one thing per press, in this order: cancel a running search → close the detail view or help → clear the search, then the filter → nothing. It never quits |
| `q` | Leave the detail view. Quit from the main view |
| `Ctrl+C` | Quit from anywhere |
| `Ctrl+Z` | Suspend |

How filters work:
- **Syntax:** plain words match anywhere in the line (lowercase ignores case, any capital makes it case-sensitive). You can also use `key=value`, `key~regex`, `level>=warn`, and `!term` to exclude. Separate terms with spaces; every term must match.
- **Live:** filters keep following, so new matching lines stream in.
- **No mouse capture by default:** it would break tmux's copy-and-select. `--mouse` turns it on.
- **Safe in tmux and Zellij:** nothing needs Ctrl or Alt, so the multiplexer can't swallow a key.
- **Esc isn't time-sensitive:** it's never needed quickly, so tmux's `escape-time` delay doesn't matter.

## Cases you probably haven't thought of

**Messy input**
- **Lines that aren't JSON** (stack traces, startup banners, `nginx` lines): they show as `raw`. Their time column stays blank rather than showing an invented timestamp. Lines that follow one are indented under it. If any exist, the header counts them (`12 non-JSON`).
- **Different key names:** level may be under `level`, `lvl`, `severity`, or `log.level`, and pino uses numbers (30 for info, 40 for warn, 50 for error). Time may be `ts`, `time`, `@timestamp`, or seconds, milliseconds, or nanoseconds since 1970. `tailj` detects these from the first 200 lines. `--level-key`, `--time-key`, and `--msg-key` override that.
- **A message that is itself escaped JSON:** the detail view offers to expand it.
- **Very long lines:** only the first 1 MiB of a 4 MB line is parsed, and the line is marked `(truncated)`. Copying and saving still use the full original bytes.
- **Odd bytes and line endings:** invalid UTF-8 shows as `�`, CRLF endings are stripped, and emoji or CJK text are measured in screen cells. A last line with no newline is held until the newline arrives or the stream ends.

**Log injection**
- A log value containing escape codes such as `\x1b]52;…` could rewrite your clipboard or redraw your screen. `tailj` shows every control character visibly (`\x1b`) and never sends one raw to a terminal.
- Output to a pipe is passed through untouched.

**Pipes and scripts**
- **Output is never re-encoded.** Filter mode writes the original bytes. Re-encoding would reorder keys and corrupt numbers larger than 2^53.
- **Exit codes follow `grep`:** 0 if anything matched, 1 if nothing did, 2 on error.
- **Piped into `head`:** when the reader closes early, `tailj` exits quietly with no stack trace.
- **Color:** none when stdout isn't a terminal, and none when `NO_COLOR` is set. `--color=always` overrides.
- **No input at all:** if stdin is a terminal and no file is given, it prints usage instead of hanging.
- **A bad path:** a missing file or permission error is reported before the full screen opens, with exit code 2, so the screen doesn't flash.
- **The producer's fate is tied to the viewer.** If you run `./service | tailj`, then while `tailj` is suspended with `Ctrl+Z` the pipe fills and the service blocks. When you quit, the service's next write fails with a broken pipe. Reading never waits on drawing, which narrows the risk but can't remove it. The help screen says to tail a file instead.

**Volume and memory**
- **Memory is capped.** It keeps the latest 100,000 lines (`--buffer`), loads the last 10,000 of a file at startup, and the header says `oldest 52,310 dropped`.
- **Bursts:** screen updates are batched to about 30 per second, so a burst of 10,000 lines a second doesn't flood the SSH link. The rate shows in the header.
- **While paused,** lines keep arriving and the `▾ N new` count grows. If the lines you're looking at get dropped from memory, the view jumps to the oldest line still kept, and a message stays up until you dismiss it: `! 4,210 lines dropped while paused`.
- **Search** runs in the background over 100,000 lines and `Esc` cancels it. `n` at the last match says `wrapped to top`.

**Files and streams over time**
- **Rotation:** it follows the file by name, like `tail -F`. When the file is rotated it reopens it and shows `↻ app.log rotated`. A truncated file gets a `── file truncated ──` separator.
- **A deleted file** that doesn't come back is marked `STALE 2m · waiting for app.log`. The old lines stay on screen.
- **The source ends** (stdin closes, for example `kubectl` exits): the header switches to `ENDED`. The viewer stays open; the end of a stream isn't the user's cue to quit.
- **Empty states:** `Waiting for lines from app.log… 12s` with no spinner. With a filter on, it reads `No lines match level≥error (of 12,431) · esc clears`, and it keeps following.
- **Clock skew and time zones:**
  - **Order:** lines appear in arrival order and are never re-sorted.
  - **Zone:** the header names the time zone. Servers usually log in UTC, and people tend to read times as their own local time; `t` switches.
  - **Ticking:** in "time since the previous line" mode the screen updates once a second; otherwise it doesn't tick.

**SSH and tmux**
- **Copying** goes through OSC 52, the escape code a terminal uses to set your clipboard, which is the only route back to your machine over SSH. The status reads `sent 412 B to clipboard` rather than claiming success, because the terminal never confirms. Help lists the tmux setting needed: `set -g set-clipboard on`.
- **Color:** the default is the 16-color palette, which follows the user's own theme. Capability checks give up after 100 ms. Missing terminfo (`xterm-kitty`) falls back to `xterm-256color` behaviour.
- **Non-UTF-8 sessions:** a `LANG=C` or `POSIX` locale switches to ASCII (`...` and `|`). `--ascii` forces it.
- **Terminal restore:** on panic, `Ctrl+C`, `SIGTERM`, or `Ctrl+Z` it restores your terminal and gives back the alternate screen. A malformed line is treated as data and never ends the session.

When you build it, the parser, filter, rotation and buffer behaviour can all be tested without a terminal. Test the drawing with snapshots at 120, 80×24, 60, and 40×8, both with and without `NO_COLOR`.
