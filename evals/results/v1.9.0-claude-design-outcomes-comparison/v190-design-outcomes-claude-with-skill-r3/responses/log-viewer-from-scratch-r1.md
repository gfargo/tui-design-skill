I'm calling it `jlog` here. The design treats it as two products in one binary: it decides at startup whether it's a full-screen viewer or a plain filter. Most of what goes wrong in tools like this happens at that decision, so it comes first.

## 1. Product shape: the TTY check decides

| stdin | stdout | Mode |
|---|---|---|
| file arg or pipe | TTY | **Full-screen viewer** (alternate screen, follows by default) |
| file arg or pipe | not a TTY | **Filter mode.** No UI. Matching lines go to stdout as their **original bytes, unchanged** (`jlog --level warn app.log \| jq …` keeps working) |
| pipe | TTY | Viewer. Keys are read from `/dev/tty`, so `kubectl logs -f api \| jlog` works |
| any | not a TTY, and `--pick` | Viewer drawn on `/dev/tty`. Lines you mark are printed to stdout when you exit, like fzf |
| TTY with no file | TTY | Print usage and exit 2. Never sit waiting on the keyboard as if it were a log |

**Language:** I'd use Go with Bubble Tea. You get one static binary you can `scp` to any server, and the reader goroutine stays separate from rendering.

## 2. Screen layout

There are no boxes. The top line shows state, the bottom line shows key hints, and everything in between is log. Each record is one row: time, level, message, then the remaining fields as dimmed `key=value` pairs. Rows are truncated with `…`, not wrapped. The date and timezone appear once in the header instead of on every row.

**80×24, following (the default):**
```
api.log  2026-10-28 UTC                        FOLLOW  12,402 lines  84/s
14:02:07.118 INF request done  method=GET path=/v1/users status=200 dur=12ms
14:02:07.342 WRN slow query  table=orders rows=18211 dur=1.84s
14:02:08.001 INF request done  method=POST path=/v1/orders status=201 dur=4…
14:02:09.517 DBG cache miss  key=user:8812
14:02:11.902 ERR upstream timeout  host=pay-1 attempt=3 req_id=7f3a9c2e-…
             panic: runtime error: index out of range [3] with length 3
             goroutine 41 [running]:
q quit ⋅ / search ⋅ & filter ⋅ 1-4 level ⋅ enter detail ⋅ ? help
```
- There is **no cursor row while following**, so nothing on screen has to move with the stream.
- Lines that aren't JSON (panics, stack traces) are attached to the record before them and indented under the time column. The indentation is the only marker.

**80×24, paused and filtered:**
```
api.log  & level>=warn status>=500  342/12,402      PAUSED  ▾ 37 new  G follow
14:01:52.410 WRN slow query  table=orders rows=18211 dur=1.84s
14:02:11.902 ERR upstream timeout  host=pay-1 attempt=3 req_id=7f3a9c2e-…
14:02:15.077 ERR payment declined  status=502 provider=acme req_id=19be…
q quit ⋅ / search ⋅ & filter ⋅ enter detail ⋅ space mark ⋅ y copy ⋅ ? help
```
Any upward movement pauses the view. A cursor appears, shown in reverse video and nothing else, and the screen stops moving while you read. `▾ 37 new` counts the matching lines that arrived since you paused.

**Detail view (Enter).** Below 140 columns it replaces the list. `Esc` goes back to where you were.
```
14:02:11.902 ERR upstream timeout                      record 12,388/12,402
  ts        2026-10-28T14:02:11.902Z
  level     error
  host      pay-1
  attempt   3
  req_id    7f3a9c2e-51b0-4d0e-9a77-2c1d0b6e4f10
  err       {
              "code": "ETIMEDOUT",
              "after_ms": 5000
            }
  (raw)     panic: runtime error: index out of range [3] with length 3
            goroutine 41 [running]:
esc back ⋅ [ ] prev/next ⋅ = filter on ⋅ - exclude ⋅ y copy ⋅ ? help
```

**140 columns and wider.** The detail pane stays open beside the list (shown at half scale). A single `│` rule is the only line drawn:
```
api.log  2026-10-28 UTC                    PAUSED ▾ 37 new  12,402 lines
14:02:07.118 INF request done  method=GET …  │ host      pay-1
14:02:11.902 ERR upstream timeout  host=p…   │ attempt   3
14:02:15.077 ERR payment declined  status…   │ req_id    7f3a9c2e-51b0-…
q quit ⋅ / search ⋅ & filter ⋅ tab focus ⋅ ? help
```

**60 columns (a tmux split):**
```
api.log  FOLLOW  12,402  84/s
14:02:07 INF request done  method=GET path=/v1/use…
14:02:07 WRN slow query  table=orders rows=18211 d…
14:02:11 ERR upstream timeout  host=pay-1 attempt=…
/ search ⋅ & filter ⋅ enter detail ⋅ ? help
```

### Floor pressure test
- **140+ columns:** list and detail side by side.
- **80–139 columns:** list only. Detail opens with Enter.
- **60–79 columns:** milliseconds, date, and rate leave the header. Hints are cut from the right, but `? help` always stays.
- **Header when space runs out:** the filter text is truncated first. The match count and FOLLOW/PAUSED are never truncated.
- **50–59 columns:** extra fields are hidden and only the message shows. Enter still shows every field.
- **Under 50 columns:** the time column is dropped. Time is still in the detail view.
- **Under 40×6:** the screen reads `terminal too small: need 40x6, q to quit`. Reading continues in the background, so nothing is lost while it's too small.

### Clutter audit (of this design)
- **Border depth:** 0. The only drawn line is the `│` at 140+ columns.
- **Level:** shown two ways, a 3-letter word (`ERR`) plus color. There are no icons or row tints, and it stays readable under `NO_COLOR`.
- **Markers on every row:** none. The selection marker only exists while paused, and continuation lines are marked by indentation alone.
- **Chrome:** 2 of 24 rows. The date and timezone that would otherwise repeat on every row (~11 cells × 22 rows) appear once in the header.

## 3. Key bindings

The scheme mixes arrow keys with vim-style aliases. Nothing depends on Ctrl+B (tmux), Ctrl+A (screen), or Alt.

| Key | Action |
|---|---|
| `j`/`k`, `↓`/`↑` | Move one line. Moving up pauses |
| `Ctrl+D`/`Ctrl+U`, `PgDn`/`PgUp` | Move half a page / a full page |
| `g` / `G` (`Home`/`End`) | Jump to oldest in buffer / jump to newest **and resume following** |
| `F` | Toggle follow (same as `less`) |
| `/` then `n`/`N` | Search. Starts at the newest line and goes back in time. `n` = older, `N` = newer. Shows `(3/41)` |
| `&` | Filter (same as `less`). Only matching lines are shown, and new matches keep arriving |
| `1` `2` `3` `4` | Minimum level: all / info+ / warn+ / error+ |
| `Enter` | Open detail |
| `[` / `]` | Previous/next record (in detail) |
| `=` / `-` | In detail, on the selected field: add `field=value` to the filter, or exclude it |
| `w` | Toggle wrap. Off by default |
| `h`/`l`, `←`/`→`, `0` | Scroll sideways when not wrapping, `0` resets |
| `x` | Show/hide the extra fields |
| `Space` | Mark a line |
| `y` | Copy the record, or all marked records, as NDJSON |
| `s` | Save the current filtered buffer to a file (asks for a name, default `./jlog-20261028-140211.ndjson`) |
| `Ctrl+L` | Full redraw, for when SSH garbles the screen |
| `?` | Help: every key, grouped by view |
| `Esc` | One step back: close help → cancel search → clear filter → leave detail. **Never quits** |
| `q` | Leave detail, or quit from the list. No confirmation, since nothing is lost |
| `Ctrl+C` | Quit from anywhere |
| `Ctrl+Z` | Suspend through the framework, redraw on `fg` |

**Filter syntax:** keep it small.
- A bare word matches anywhere in the raw line. Case-insensitive unless you type a capital (smart case).
- `key=v`, `key!=v`, `key>=500`, and `key~regex` match fields. Nested fields use dots: `req.status>=500`.
- Spaces mean AND.

The same syntax works as `--filter` on the command line.

## 4. Cases you probably haven't covered

**Piping and scripting**
- **Filter mode passes lines through unchanged.** It doesn't reformat them. `--format pretty` gives human-readable lines for scripts, logs, and screen readers, but it's opt-in.
- **Flush after every line,** so `jlog … | grep` shows results immediately.
- **When the consumer exits early (`| head`),** exit quietly with no stack trace.
- **Exit codes follow grep** when used with `--no-follow`: 0 = something matched, 1 = nothing matched, 2 = error. That makes `jlog --no-follow --level error app.log && page-oncall` work.
- **Never page or color piped output.** Color is decided separately for each output stream. `NO_COLOR` is respected.

**The input itself**
- **Keep reading stdin even while paused.** If `jlog` stops reading a pipe, the pipe fills and the *service writing the logs blocks*. Pausing only stops the display. Ctrl+Z truly stops reading, so when the input is a pipe the help text warns that suspending stalls the upstream writer.
- **Don't parse half-written lines.** The last line of a file is often still being written. Wait for the newline.
- **Log rotation and truncation.** Follow the file by name, like `tail -F`. When the file is rotated, insert a dim divider row: `rotated app.log at 14:02:11`. When the file is deleted, the header shows `waiting for app.log` and the last lines stay on screen, dimmed.
- **When the stream ends** (the process died, or `kubectl` disconnected): the header shows `ENDED 14:03:12`. Stay open, because that's usually when people start reading.
- **Large files.** On startup read only the last `-n 1000` lines, like `tail`. Never load a 4 GB file. `g` goes to the oldest line *in the buffer*, and the header says how much of the file that covers.
- **Memory cap.** Keep at most 100k lines, oldest dropped first, and say so: `oldest 52,310 dropped`. If you're scrolled into a region that gets dropped, snap to the oldest line still kept. Don't jump to the bottom.
- **Very long lines** (a 3 MB JSON blob): parse at most 1 MiB per line and show `[line 3.1 MB, truncated]`.

**Messy JSON**
- **Field names vary between loggers.** Try `ts`/`time`/`timestamp`/`@timestamp`, `level`/`lvl`/`severity`, and `msg`/`message`. Pick from the first 200 lines, and allow overrides with `--time-key`, `--level-key`, and `--msg-key`.
- **Levels vary too.** Some loggers use numbers (pino's `30` = info, `50` = error), and case varies. Unknown levels show their first 3 characters, uppercased.
- **Timestamps** can be RFC 3339 or epoch seconds, milliseconds, or nanoseconds. Show them in the zone named in the header. `--utc` switches to UTC.
- **Lines that are valid JSON but not objects** (`"hello"`, `[1,2]`) are treated as raw text.
- **Keep arrival order.** Several sources with skewed clocks will look out of order. Don't sort. Re-sorting under a reader is worse.

**Hostile content**
- **Escape sequences in the logs.** A log line containing escape codes can recolor the screen, change the window title, or write to the clipboard. In the viewer, show control characters as visible text (`\x1b`, `\n`). Filter mode still outputs the original bytes.
- **Invalid UTF-8** is shown as `\xNN`.
- **CJK text and emoji** are measured by display width, not character count. Otherwise columns go crooked.

**SSH and tmux**
- **Mouse capture is off by default,** so drag-to-select and tmux copy mode keep working. Use `--mouse` to turn it on.
- **`y` copies over SSH with OSC 52.** tmux needs `set -g set-clipboard on`, which is in the docs. When the copy can't be confirmed, the status line says `copied (if your terminal allows OSC 52); s to save to file instead`.
- **Nothing waits on the Esc key,** because tmux can delay it.
- **No animation or spinners.** Redraw only cells that changed, at most about 30 times a second. At 10k lines/s the header shows the rate, and rows are batched rather than drawn one by one.
- **Colors** use the 16-color theme unless truecolor is detected or set by the user. Over SSH, `COLORTERM` usually doesn't arrive.
- **If the SSH connection drops,** restore the terminal and exit cleanly. Inside tmux the session simply persists.

**Display states**
- **No matches:** `No lines match "level>=warn status>=500" in 12,402 lines. Esc clears the filter.` A blank screen is never shown.
- **Paused selection** is tied to a record ID, not a screen row, so new lines and dropped lines never move what you're looking at.
- **Multiple files** (`jlog a.log b.log`): a source column appears only when there's more than one source.
- **Accessibility:** `TERM=dumb`, `--plain`, or `JLOG_PLAIN=1` streams `--format pretty` output as appended lines. Level words are always printed, and nothing is redrawn in place.

## 5. Tests worth pinning
- **Unit tests:** field detection, level mapping, the filter parser, partial-line handling, ring-buffer anchoring.
- **Golden frames** at 140×40, 80×24, 60×20, and 39×5, with color and with `NO_COLOR`.
- **Filter mode:** byte-identical passthrough, the 0/1/2 exit codes, and `| head` exiting quietly.
- **One PTY smoke test:** start with a pipe as input, pause, keep feeding 10k lines, and check that the writer never blocks and that the terminal is restored on Ctrl+C.
