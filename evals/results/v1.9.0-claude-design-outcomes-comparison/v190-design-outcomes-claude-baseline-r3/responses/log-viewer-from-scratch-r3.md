# `jtail`: a terminal viewer for JSON-lines logs

The design starts from four constraints:

1. **Narrow panes come first.** Wide terminals just get more columns.
2. **Assume nothing about the terminal.** Use only 16 ANSI colors and work fully in ASCII. Don't rely on mouse support, the Alt key, function keys or a clipboard.
3. **Pipes get plain data, not a screen.** If stdout isn't a terminal, there is no interface; `jtail` acts as a filter.
4. **Never lose your place.** New lines must not move what you're reading.

---

## 1. Screen layout

### Normal width (80+ columns)

```
14:02:11 INF api    GET /orders 200            dur=12ms user=4821 req=a9…
14:02:11 WRN api    slow query                 dur=1840ms table=orders
14:02:12 ERR worker job failed: timeout        job=8812 attempt=3    [+14]
14:02:12 ~   -      panic: runtime error: index out of range
14:02:13 INF api    GET /health 200            dur=1ms
14:02:13 DBG api    cache miss                 key=user:4821
──────────────────────────────────────────────────────────────────────────
FOLLOW  app.log  lvl>=info  /timeout 1/3  svc=api      12,408  41/s  ?=help
```

- **Columns:** time, level, an optional source/service field, message, then the remaining fields as `key=val` until the line runs out. A `…` marks cut-off text.
- **Level** is always a 3-letter tag (`DBG INF WRN ERR FTL`). Color is extra, so the level is still readable with `NO_COLOR` or a monochrome terminal.
- **`[+14]`** means the entry has a multi-line continuation, such as a stack trace. It shows up in the detail view.
- **`~`** marks a line that isn't valid JSON. It is shown dimmed, exactly as it was written.
- **The status bar is the bottom line**, as in `less`, next to where your eyes already are. Prompts for search and filter also open there.

### Narrow pane (about 40–59 columns)

```
E job failed: timeout job=8812 at…
W slow query dur=1840ms table=ord…
I GET /orders 200 dur=12ms user=4…
~ panic: runtime error: index out…
──────────────────────────────────
PAUSED +1,284  lvl>=info  f:2  ?
```

The layout changes at fixed widths:

| Width | What's shown |
|---|---|
| 100 or more | Full time, level, source, message, fields |
| 60–99 | `HH:MM:SS`, 3-letter level, message, fields. Source is dropped unless pinned. |
| 40–59 | 1-letter level, message, fields. Time is dropped; `T` brings it back. |
| Under 40 | Message only. The status bar shrinks to the mode plus a count. |
| Under 3 rows | Status line only. |

### Detail view (`Enter`)

Under 100 columns it replaces the list. At 100 or more it opens as a right-hand split.

```
< 8,812/12,408                 ERR
time      2026-10-28T14:02:12.331Z
level     error
msg       job failed: timeout
job       8812
attempt   3
err.type  TimeoutError
err.stack
  at runJob (worker.js:88:11)
  at process (queue.js:41:5)
──────────────────────────────────
f:filter  x:exclude  y:copy  Esc
```

- Time, level and message come first. All other keys are sorted A–Z.
- Nested objects are flattened to dotted paths (`err.type`, `http.status`). Arrays are shown as `[0]`, `[1]` and so on.
- `j`/`k` move between fields. Pressing `f` on a field adds `field=value` as a filter, so the error you're looking at becomes a filter.

---

## 2. Key bindings

The keys follow `less` and vim, because that's what people already type over SSH. I avoided Alt and function keys and Ctrl-S/Ctrl-Q (flow control). Every Esc action also has a non-Esc key, because tmux's `escape-time` setting can make Esc feel slow.

**Moving around**

| Key | Action |
|---|---|
| `j` / `k`, arrow keys | Line down / up |
| `Space` / `b`, `PgDn` / `PgUp` | Page down / up |
| `d` / `u` | Half page down / up |
| `g` | Go to the oldest line in the buffer |
| `G` or `F` | Go to the bottom and **resume follow** |
| Any upward movement | **Pauses** follow |

**Search** (highlights matches and keeps the surrounding lines)

| Key | Action |
|---|---|
| `/` | Search forward |
| `?` | Search backward. On an empty prompt it opens help. |
| `n` / `N` | Next / previous match |

**Filter** (hides lines that don't match)

| Key | Action |
|---|---|
| `&` | Add a filter, e.g. `svc=api`, `status>=500`, `msg~timeout`, `-user=bot` |
| `l` / `L` | Raise / lower the minimum level |
| `-` | Remove the most recent filter |
| `=` | List active filters; delete them one at a time with `x` |
| `0` | Clear all filters and search |

**View**

| Key | Action |
|---|---|
| `Enter` | Open the detail view |
| `Esc`, `h` or `Backspace` | Go back |
| `w` | Toggle wrapping long lines |
| `T` | Cycle time display: original → local → UTC → relative (`3s`) → hidden |
| `c` | Choose which fields become columns |
| `r` | Show raw JSON instead of the formatted line |
| `Ctrl-L` | Redraw (useful after SSH glitches) |

**Output**

| Key | Action |
|---|---|
| `y` | Copy the current entry as raw JSON using OSC 52 (works over SSH if the terminal and tmux allow it) |
| `\|` | Pipe the current entry, or the whole filtered view, into a shell command (`\| jq .err`) |
| `s` | Save the filtered view to a file as raw JSON lines |
| `E` | Show the **equivalent command line** for the current filters, e.g. `jtail --level warn -F 'svc=api' app.log` |
| `q` / `Ctrl-C` | Quit. Inside the detail view, `q` goes back instead of quitting. |

`E` exists because the usual workflow is: explore interactively, then want the same thing in a script.

---

## 3. Piping and modes

| stdin | stdout | Behavior |
|---|---|---|
| file argument | terminal | Interactive viewer; follows by default |
| pipe | terminal | Interactive viewer; keys are read from `/dev/tty` |
| anything | pipe or file | **Filter mode**: no interface, no colors |

- **Filter mode** outputs the **original JSON lines, byte for byte**, so `jtail --level error app.log | jq …` works. Use `--format=text` to get the formatted columns instead.
- It reads to the end and exits unless you pass `-f`, the same as `tail`.
- **Exit codes** work like grep: 0 if anything matched, 1 if nothing matched, 2 on error.
- When the next program in the pipe closes early (`| head`), `jtail` exits quietly with status 0, with no "broken pipe" error.
- Every interactive filter has a matching flag (`--level`, `-F expr`, `-e search`), which is what `E` uses.

---

## 4. Cases you probably haven't thought of

### The log data itself

- **Escape sequences in log content.** A log line containing `\x1b]52;…` or `\x1b[2J` could rewrite your clipboard or clear your terminal. All control characters are shown as visible text (`\x1b`, `\r`), never sent to the terminal. Raw output in filter mode leaves bytes unchanged, since that's the user's explicit choice.
- **Field names vary by logger.** Time is read from `ts`, `time`, `timestamp`, `@timestamp` or `t`. Level from `level`, `lvl`, `severity` or `levelname`. Message from `msg`, `message` or `@message`. pino/bunyan numeric levels (30 = info, 50 = error) are converted. The detected mapping appears in help, and `--time-key` and similar flags override it.
- **Timestamp formats.** Epoch seconds, milliseconds and nanoseconds are told apart by size. Strings are used as written by default, so nothing gets silently shifted to another time zone.
- **Large integers** such as IDs or trace numbers are kept as text, not converted to floating-point numbers that lose precision. `id=9007199254740993` stays exact.
- **Huge lines.** Parsing stops at 1 MB per line. The entry is marked `[truncated]`; the full raw line is still available through `\|` or `s` when reading from a file.
- **Non-JSON lines.**
  - Lines starting with whitespace (stack traces) are attached to the previous entry as `[+N]`. Other non-JSON lines become standalone `~` entries.
  - Field filters hide non-JSON lines; free-text search still finds them.
  - The status bar counts them, so "10% of your logs aren't JSON" is visible.
- **Line-format problems.**
  - Lines ending in CRLF and files starting with a byte-order mark are handled.
  - Invalid UTF-8 is shown as `\xNN`.
  - Duplicate keys: the last one wins, and the detail view shows `(dup)`.
  - A **partial last line** (the writer hasn't sent the newline yet) is held back for 250 ms, so a half-written entry isn't shown as invalid JSON.

### Files and streams

- **Log rotation.**
  - Files are tracked by inode. If a file is renamed by logrotate, `jtail` finishes reading the old file, then reopens the path when a new file appears.
  - If a file shrinks (copytruncate), it starts from the beginning again.
  - Either way, a divider is inserted in the list, e.g. `── rotated 14:02:11 ──`.
- **File deleted and not replaced.** The status bar shows `GONE, waiting`. Everything already loaded stays readable.
- **Startup.** The last 1,000 lines are loaded, like `tail`. `-n all` loads the whole file; for files, it stores line positions rather than contents, so multi-GB files still open instantly.
- **Memory cap.** Input from a pipe can't be reread, so it is kept in a ring buffer (default 200k entries or 256 MB). If you're scrolled to the top while old lines are being dropped, a banner says so instead of the screen moving under you.
- **Multiple files** (`jtail a.log b.log`). Lines are interleaved in **arrival order** with a short source label. They are not re-sorted by timestamp, because that would make a live tail look like the past is changing.

### Load and display

- **Bursts** of thousands of lines per second. Screen updates are capped at about 20 per second, and only changed lines are redrawn, which matters on slow SSH links. The rate (`41/s`) is in the status bar.
- **Paused while reading.** New lines never move the screen. The status bar shows `PAUSED +1,284` and the count keeps rising; `G` jumps back to the bottom.
- **Filter changes keep your place.** The view stays anchored on the line you were looking at (or the nearest one that still matches), instead of jumping to the top or bottom.
- **Wide characters and emoji** are measured by display width, so columns don't shift. If the locale isn't UTF-8, everything falls back to ASCII: `...` instead of `…` and `-` for the divider.
- **Terminal capabilities.** With `NO_COLOR`, `TERM=dumb` or no color support, the levels are still readable from their text tags.
- **Resizing** (tmux pane changes) reflows the layout immediately, without losing your position.

### Sessions

- **SSH drop (SIGHUP).** The terminal is restored and `jtail` exits cleanly. Under tmux the session survives as usual.
- **`Ctrl-Z` suspend and `fg` resume** both work. Input received while suspended is kept and shown as `+N`.
- **Clipboard over SSH.** OSC 52 needs `set -g set-clipboard on` in tmux, and some terminals block it. Because `y` might silently do nothing, `\|` and `s` are always there as reliable alternatives.
- **Time zones.** On remote servers "local" usually means UTC, which is not your time zone. The default is to show timestamps as written in the log, and the status bar labels the current time mode whenever it isn't "original".
