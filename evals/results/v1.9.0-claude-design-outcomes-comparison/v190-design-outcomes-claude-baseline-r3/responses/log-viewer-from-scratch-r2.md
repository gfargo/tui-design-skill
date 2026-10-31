# `jtail`: a terminal viewer for JSON-lines logs

I designed for the hardest case first: a 60-column tmux pane over a slow SSH link. Each choice below also has to work when the output goes into a pipe. On wider screens the layout simply adds more.

---

## 1. Screen layout

### Narrow pane (~60 cols), the default design target

```
api.log  FOLLOW  ≥info  12,408 ln  41/s  UTC
────────────────────────────────────────────────────────────
14:02:11 INF request done path=/v1/users status=200 dur=1…
14:02:11 WRN slow query table=orders dur=1.204s
14:02:12 ERR upstream timeout svc=billing attempt=3
14:02:12 INF request done path=/v1/orders status=200 du…
14:02:12 ··· panic: runtime error: index out of range
14:02:12 ···   goroutine 41 [running]:
──────────────── marked 14:02:13 ───────────────────────────
14:02:13 INF healthcheck ok
14:02:13 DBG cache miss key=user:8812
────────────────────────────────────────────────────────────
/ search  & filter  ⏎ detail  ? help
```

### Paused (you scrolled up, or pressed `f`)

```
api.log  PAUSED +342 new  ≥warn svc=billing  88/12,408  UTC
────────────────────────────────────────────────────────────
...
14:01:58 ERR upstream timeout svc=billing attempt=1
> 14:02:12 ERR upstream timeout svc=billing attempt=3   ◀ cursor
...
────────────────────────────────────────────────────────────
G resume  n/N next/prev  ⏎ detail  ? help
```

### Detail view

At narrow widths the detail view replaces the list. It becomes a side split only at 120 cols or more.

```
ERR 2026-10-28T14:02:12.481Z            line 9,114 of 12,408
────────────────────────────────────────────────────────────
msg      upstream timeout
svc      billing
attempt  3
req_id   9f2c1e7a-44b0-4c1e-9d3b-0a7e5c1f2d88
err      ▾
  type     DeadlineExceeded
  stack    ▸ (14 lines)
user_id  90071992547409931
────────────────────────────────────────────────────────────
q back  y copy JSON  ⏎ fold  + add as column  j/k field
```

### Wide (≥120 cols)

Columns are list on the left and detail on the right, split by `│`. The header also shows the file path, the buffer usage (`buf 41%`), and the time zone.

### Row rendering rules

These rules apply at every width.
- Field priority is **time → level → msg → extra fields in source order**. Fields are dropped from the right until the row fits, and a cut is marked with `…`. Rows don't wrap unless you turn wrap on with `w`.
- Under 50 cols the time column shrinks to `:11` (seconds only). Under 35 cols the time disappears and only level and message are shown. Under 20 cols or 3 rows the screen shows `jtail: 18x2 too small` and keeps buffering input.
- Level is always a 3-letter text label (`ERR`), so it reads correctly without color. Color is extra on top of that.
- Non-JSON lines are shown dimmed with a `···` level marker. Indented continuation lines, such as stack traces, stay grouped under the line that came before them.
- The header and footer are each one line. `--no-chrome` removes both for very small panes.

---

## 2. Key bindings

These are close to less and vim, because that's what people already type over SSH.

| Key | Action |
|---|---|
| `j`/`k`, `↓`/`↑` | Move cursor (pauses follow) |
| `Ctrl-d`/`Ctrl-u`, `space`/`b` | Half page / full page |
| `g` / `G` | Top of buffer / bottom **and resume follow** |
| `f` | Toggle follow/pause |
| `/` `n` `N` | Search: highlight matches and jump to next/prev |
| `&` | Filter: hide rows that don't match (less convention) |
| `1`–`5` | Minimum level: trace, debug, info, warn, error |
| `Enter` | Open detail / fold or unfold a field inside detail |
| `q` / `Esc` | Back one level; on the main list, quit |
| `m` | Insert a "marked HH:MM:SS" divider (like pressing Enter during `tail -f`) |
| `w` | Toggle wrap |
| `t` | Cycle time display: UTC → local → relative (`-3.2s`) |
| `c` | Choose which fields appear as columns |
| `y` | Copy the current line's raw JSON (OSC 52, so it works over SSH and tmux) |
| `\|` | Pipe the current filtered view to a shell command (`\| jq .req_id \| sort -u`) |
| `s` | Save the filtered view to a file (raw lines) |
| `Ctrl-l` | Full redraw |
| `?` | Help overlay |

**Filter syntax.** One small language serves both `&` and `--filter`:
`level>=warn svc=billing status!=200 dur>1s err.type~Deadline "exact phrase" /re.ge?x/`
Terms separated by spaces are ANDed, `or` is spelled out, and dotted paths reach into nested objects.

**Keys deliberately left unbound:**
- `Ctrl-s`/`Ctrl-q`: XON/XOFF flow control can freeze the session.
- `Ctrl-b`/`Ctrl-a`: tmux and screen prefixes.
- `~`: the SSH escape character after a newline.
- All `Alt-` combinations: unreliable through SSH and tmux.

Because `Esc` is ambiguous under tmux's `escape-time`, every `Esc` action also has a plain-letter equivalent (`q`).

---

## 3. Piping and non-TTY behavior

| stdin | stdout | Behavior |
|---|---|---|
| file arg | TTY | Full TUI that follows the file by name (`tail -F` semantics) |
| pipe | TTY | Full TUI, with keys read from `/dev/tty` |
| any | **pipe/file** | **No TUI.** Works as a streaming filter. |
| any | TTY, `TERM=dumb` | Plain formatted lines, no cursor control |

- **Filter mode** takes the same flags as the keys: `--level warn --filter 'svc=billing' --since 10m`. By default it writes the **original bytes unchanged**, so `jtail ... | jq` gets valid JSON. `--format=text` gives the pretty single-line form, and `--fields a,b` gives TSV.
- `--follow` keeps a filter-mode run going after the end of the file. Without it, a file argument ends at EOF.
- `jtail app.log | head -5` exits quietly when the pipe closes. It prints no "broken pipe" error and exits with status 0.
- Exit codes: 0 means OK, 1 means nothing matched (same as grep, so it works in scripts), 2 means a usage or filter syntax error.

---

## 4. Cases you probably haven't thought of

### Untrusted content
- **Escape sequences inside log values.** A value such as `"\u001b]52;c;..."` could rewrite your clipboard, change the terminal title, or hide lines. All C0/C1 control characters are shown escaped as visible text (`\x1b`), both in the TUI and in `--format=text`. Raw passthrough mode leaves the bytes untouched because its output is meant for programs, not a screen.
- **Unicode width.** CJK characters, emoji, and zero-width joiners are measured by display width, so columns stay aligned. Bidi override characters (U+202E and similar) are escaped.

### Messy input
- **Field names differ by library.** Level is read from `level`, `lvl`, `severity`, or `log.level`. Numeric levels from pino and bunyan (30, 40, 50) are mapped to names. Time is read from `time`, `ts`, `timestamp`, or `@timestamp`. Epoch values are classified as s, ms, µs, or ns by their magnitude. The header shows which field was picked (`time←ts`), and `--time-field` and `--level-field` override it.
- **No level or no time.** The row shows `---` in that column and still appears in the list. A level filter hides these rows unless you add `--keep-unleveled`.
- **Big integers** such as `90071992547409931` are kept as their original text. They never go through a float conversion, which would silently change the digits.
- **Duplicate keys** are all shown in the detail view. Filters use the last one, which matches what most parsers do.
- **Very long lines** (a 4 MB line from someone logging a whole request body): up to 1 MB is parsed. Past that, the row reads `[truncated 4.1 MB]`, and `y` and `s` still output the full raw line.
- **Partial last line** (the writer hasn't sent the newline yet): it is held back until the newline arrives. On EOF or a 2-second pause it is shown dimmed as partial.
- **Out-of-order timestamps.** Rows always appear in arrival order and are never re-sorted. In relative time mode, a timestamp that goes backwards gets a `↶` marker.

### Files and streams
- **Rotation.** If the file is renamed or recreated, it is reopened by name and a `── rotated ──` divider is inserted. If the file is truncated (size smaller than the read offset), a `── truncated ──` divider is inserted and reading starts again from 0.
- **File deleted and not recreated.** The header shows `api.log (gone)` and the viewer keeps waiting rather than exiting.
- **Huge existing file.** On open, only the last 10k lines are read, starting from the end. `--from-start` reads the whole file. Pressing `g` at the top of the buffer loads older lines on request.
- **Memory.** The ring buffer holds 200k lines or 256 MB by default. When old lines are evicted, the top of the buffer shows `older lines dropped`.
- **Eviction under a paused cursor.** The cursor is pinned to a line ID, not a screen position. If that line is evicted, the cursor moves to the oldest remaining line and the footer briefly shows `your line left the buffer`.
- **Bursts (10k lines/s).** Input is always read at full speed, but the screen redraws at most 20 times per second and only sends the parts that changed. This matters over SSH, because flooding the link makes your keystrokes lag. The rate shown in the header comes from input, not from redraws.
- **Pausing never drops data.** The `+342 new` counter keeps rising, and `G` jumps to live again.

### Terminal and session
- **Resize, including tmux pane zoom.** Columns are recalculated immediately and the cursor stays on the same line.
- **SSH drops (SIGHUP), Ctrl-C, or a crash.** The terminal is restored: alternate screen exited, cursor shown, raw mode off. A dead session must never leave the shell unusable.
- **Ctrl-Z** suspends cleanly, and `fg` redraws.
- **Mouse is off by default.** Turning it on breaks tmux's native text selection and adds SSH traffic. `--mouse` enables it.
- **Color.** `NO_COLOR` is respected. Only the 16 basic ANSI colors are used, so the viewer follows your terminal theme and stays readable on light backgrounds.
- **No spinners or animation.** Constant redraws are noise over a slow link.

### Empty and failed states
- **No input yet:** `waiting for input on stdin…` or `waiting for api.log…`
- **Filter matches nothing:** `0 of 12,408 match svc=bilin`, followed by `no field "svc" has value "bilin"; did you mean "billing"?` when there is an obvious near match.
- **Invalid filter or regex:** the error is shown inline at the input line with a caret under the problem character. The previous filter stays active.
- **All input is non-JSON:** after 50 lines it shows `no JSON seen; showing raw lines (search still works)`, so it's clear the viewer isn't broken.

### Out of scope on purpose
- **Multiple files and merging by timestamp.** Use `tail -F a.log b.log | jtail`. That keeps arrival order and keeps the tool simple.
