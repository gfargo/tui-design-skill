I've read the skill's guidance on layout, keys, terminal and SSH behavior, and output streams; writing the design now.

# jtail: a JSON-lines log viewer

**Recommendation:** jtail is one binary with two modes, and the choice is made automatically. If stdout is a terminal, it opens a full-screen, single-pane viewer that follows new lines like `tail -f`. If stdout is piped, it runs as a plain filter that writes the matching lines unchanged, so `jq` and `grep` work on them. The layout is one list of records. Pressing Enter opens a record's full details. It has no boxes or side panels by default, so a 60-column tmux pane is a supported size. I'd build it in Go with Bubble Tea, because a single static binary is easy to `scp` onto a server.

## How it's invoked

| Invocation | stdin | stdout | Behavior |
|---|---|---|---|
| `jtail api.log` | tty | tty | Full-screen viewer that follows the file |
| `kubectl logs -f x \| jtail` | pipe | tty | Full-screen viewer; keys are read from `/dev/tty` |
| `jtail api.log -f 'level>=warn' \| jq .` | any | pipe | No UI. Matching lines go to stdout **unchanged, byte for byte**, flushed after every line |
| `jtail --plain api.log` (or `JTAIL_PLAIN=1`) | any | tty | Formatted lines are appended to normal output instead of a full-screen view. For screen readers, `script`, and `mosh` |
| `jtail` with no input | tty | — | Prints usage and exits 2. It never sits waiting on the keyboard |

- Filter options like `-f`/`--filter`, `--level`, and `--since` work the same in every mode.
- Piped output is never re-serialized, so key order, number formatting, and unknown fields survive.
- When the reader on the other end closes the pipe (`| head`), jtail exits quietly with code 0 or 141 and never prints a stack trace.

## Screen layout

Every size uses the same structure: one header row, the record list, and one footer row. There are no borders. The selected row is shown in reverse video (written as `▌` in the sketches below).

**Standard width, 80×24 (excerpt):**

```
 api.log  FOLLOWING  level>=warn svc=checkout          1,204/48,112   52/s
 14:02:07.118 WRN payment retry scheduled         attempt=2 order=8812 de…
 14:02:07.402 ERR card authorization failed       order=8812 code=do_not_…
▌14:02:08.020 ERR upstream timeout after 3000ms   peer=pay-gw:443 order=8…
 14:02:09.551 WRN slow query                      ms=1840 table=orders
 ── not json (4 lines) ─────────────────────────────────────────────────
     at Object.authorize (/srv/pay.js:88:11)
 ── Wed 2026-10-29 ─────────────────────────────────────────────────────
 00:00:01.004 WRN cert expires in 6d              host=pay-gw
 j/k move ⋅ / search ⋅ f filter ⋅ enter detail ⋅ F pause ⋅ ? help
```

- **Header:** source, follow state, active filter, matching/total line count, and arrival rate.
- **Each row:** time, level, message, then extra `key=value` fields in dim text, cut off with `…` when they don't fit.
- **The date is not repeated on every row.** A separator row appears when the day changes.
- **Level** is shown as a three-letter word (`ERR`/`WRN`/`INF`/`DBG`), with color as a second cue. It still reads correctly under `NO_COLOR`.

**Paused (you scrolled up):** the header changes and the footer leads with the way back to following.

```
 api.log  PAUSED ▾ 37 new  level>=warn svc=checkout   1,204/48,112   52/s
 ...
 G follow ⋅ / search ⋅ f filter ⋅ enter detail ⋅ ? help
```

**60-column tmux split.** This is the floor, and it's fully supported:

```
 api.log  FOLLOWING  level>=warn…          1,204/48,112
 14:02:07 WRN payment retry scheduled attempt=2 ord…
 14:02:07 ERR card authorization failed order=8812 …
▌14:02:08 ERR upstream timeout after 3000ms peer=pa…
 14:02:09 WRN slow query ms=1840 table=orders
 j/k move ⋅ f filter ⋅ enter detail ⋅ ? help
```

What gives way, in order:
1. Milliseconds drop from the time.
2. The rate (`52/s`) drops from the header.
3. The filter text is cut off. Its full text is shown in the filter prompt.
4. Extra fields shrink first. The message keeps at least 20 columns.
5. Footer hints drop from the right, but `? help` always stays.

**Wide, 120+ columns:** Enter opens a details pane on the right instead of a full screen. The list keeps at least 70 columns and the pane at least 45. Below 120, the pane gives way to the full-screen details view.

```
 api.log  FOLLOWING  level>=warn svc=checkout       1,204/48,112  52/s │ record 41,388   ERR
 14:02:07.118 WRN payment retry scheduled   attempt=2 order=8812       │ time  2026-10-28T14:02:08.020Z
 14:02:07.402 ERR card authorization failed order=8812 code=do_not_…   │ msg   upstream timeout after 3000ms
▌14:02:08.020 ERR upstream timeout after 3000ms peer=pay-gw:443 ord…   │ svc   checkout
 14:02:09.551 WRN slow query                ms=1840 table=orders       │ peer  pay-gw:443
                                                                       │ err.stack
                                                                       │   Error: ETIMEDOUT
 j/k move ⋅ / search ⋅ f filter ⋅ = only value ⋅ - exclude ⋅ esc close ⋅ ? help
```

**Details view (below 120 columns, full screen):**

```
 api.log › record 41,388 of 48,112                ERR  2026-10-28T14:02:08.020Z
 msg        upstream timeout after 3000ms
▌peer       pay-gw:443
 order      8812
 err.stack
   Error: ETIMEDOUT
       at TLSSocket.onTimeout (/srv/net.js:41:9)
 J/K next/prev record ⋅ = only this ⋅ - exclude ⋅ y copy ⋅ esc back ⋅ ? help
```

- Nested objects are flattened to `a.b` keys.
- Escaped `\n` inside strings becomes a real line break here. In the list it is shown as `↵`.

**Too small (below 40×6):** jtail shows `jtail needs 40×6 (now 34×5) · q quit`. It keeps reading input while this message is up.

## Key bindings

In the list, keys work without any mode switch. When a prompt is open, it takes all printable keys, so letters are just letters there. No action needs `Ctrl+B`, `Ctrl+A`, an Alt key, or a fast `Esc`, because tmux, screen, and SSH latency interfere with those.

| Key | List | Details |
|---|---|---|
| `j`/`k`, `↑`/`↓` | Move one row (moving up pauses) | Move between fields |
| `PgUp`/`PgDn`, `Ctrl+U`/`Ctrl+D` | Page / half page | Scroll |
| `g` / `G`, `Home`/`End` | Top (pauses) / bottom (**resumes following**) | Top / bottom |
| `F` | Pause or resume following, as in `less` | — |
| `/`, `n`/`N` | Search: highlights matches, jumps between them, shows `(3/41)` | Same |
| `f` (alias `&`) | Filter prompt: hides lines that don't match | — |
| `L` | Cycle the minimum level: all → info → warn → error | — |
| `]` / `[` | Next / previous WRN or ERR line | — |
| `Enter` | Open details | — |
| `J`/`K` | — | Next / previous record (within the filter) |
| `=` / `-` | — | Add `field=value` / `field!=value` to the filter |
| `c` | — | Show or hide this field as a list column |
| `w` | Wrap on/off (off by default) | — |
| `h`/`l`, `←`/`→` | Scroll sideways when wrap is off | — |
| `t` | Time display: original zone → local → relative (`3s ago`) | Same |
| `r` | Show the raw line instead of formatted text | Raw JSON |
| `y` / `Y` | Copy the raw line / just the message (via OSC 52) | Copy the record / the field value |
| `s` | Save the current filtered lines (raw) to a file. Shows a path prompt | — |
| `S` | Copy the matching shell command, e.g. `jtail -f 'level>=warn svc=checkout' api.log` | — |
| `Esc` | Close a prompt, then clear search, then clear filter. Never quits | Back to list |
| `q` | Quit | Back to list |
| `Ctrl+C` / `Ctrl+Z` | Quit / suspend (resuming catches up on what arrived) | Same |
| `?` | All keys, grouped by view | Same |

**Filter syntax.** Terms are combined with AND. Typing updates the list live. `Enter` keeps the filter, `Esc` restores the previous one, and `↑` brings back earlier filters.

| Term | Matches |
|---|---|
| `timeout` | Text anywhere in the line. Smart case: lowercase ignores case, mixed case doesn't |
| `svc=checkout`, `svc!=checkout` | A field equals / doesn't equal a value |
| `ms>1000` | A numeric comparison |
| `peer~^pay-` | A field matches a regular expression |
| `-healthz` | Excludes lines containing that text |

While a filter is active, the view keeps following and newly arriving lines that match are added.

**Mouse capture is off by default.** That way, dragging to select text and the terminal's own copy work normally in tmux and over SSH. `--mouse` turns on wheel scrolling.

## The cases you probably haven't thought of

**Input**
1. **Lines that aren't JSON** (startup banners, multi-line stack traces, a line cut off mid-write). They're shown dimmed under a `not json (N lines)` separator, never dropped, and the header counts them. `--strict` hides them.
2. **Field names differ between services.** jtail detects `msg`/`message`, `level`/`lvl`/`severity`, numeric levels (pino's 30/40/50), and time as ISO text or epoch seconds or milliseconds, based on the first 200 lines. `--msg-key`, `--level-key`, and `--time-key` override the guess. If a record has no level, it shows `---` rather than a guessed level.
3. **Log rotation and truncation.** If the file is renamed (it has a new inode), jtail reopens the new file and inserts `── rotated 14:02:11 ──`. If the file shrinks, it inserts `── truncated ──` and reads from the start. If the file is deleted and not recreated, the header shows `WAITING for api.log (gone 40s)`.
4. **The file doesn't exist yet.** jtail waits for it, like `tail -F`, instead of failing. `--no-wait` makes it exit 1 instead.
5. **The upstream program exits** (`kubectl logs -f` loses its connection). The header shows `ENDED 14:05:31 · 48,112 lines`, the view stays browsable, and nothing gets cleared.
6. **Invalid UTF-8 or binary junk** becomes `�` and jtail keeps going. A single 5 MB line is shortened in the list. The details view loads it in chunks and doesn't pretty-print anything over 256 KB unless you ask.

**Safety**
7. **Log contents can contain terminal escape sequences.** An attacker-controlled field like `user_agent` can carry codes that change the window title, write to the clipboard via OSC 52, or move the cursor. Every control character in log content is shown as visible text (`␛]52;…`) and is never sent to the terminal. Of everything in this list, this matters most.

**Volume and live updates**
8. **Very high line rates** (10k lines/s). Reading never waits on drawing, and the screen redraws at most about 30 times a second. Memory is capped (100k lines by default, set with `--buffer`). When old lines are dropped, the header says so (`oldest 52,310 dropped`), and `s` can save everything still in memory.
9. **Pausing during a burst.** Rows stay where they are while paused. If the line you're reading gets dropped from memory, the selection moves to the oldest remaining line and the status line says why.
10. **Tracking by record, not screen position.** The selection follows the record itself, not the screen row. Resizing, toggling wrap, or changing the filter keeps the same record in view.
11. **Lines arrive out of time order** (several pods merged together). They're shown in arrival order and never re-sorted live. Arrival order is what actually happened in the pipe.

**Time and place**
12. **The server's time zone isn't yours.** By default each timestamp is shown in the zone it was written in. `t` switches to local or relative time, and the header notes when the display differs from the source.
13. **Day boundaries.** A separator row appears when the date changes, so the date doesn't have to be on every row.

**Terminal and SSH**
14. **Slow SSH connections.** Only changed cells are redrawn. Terminal capability checks are skipped or time out after 100 ms. If truecolor isn't confirmed, jtail uses a 256-color palette. Colors are taken from the terminal's own palette, so they suit both light and dark themes.
15. **Copying inside tmux.** `y` uses OSC 52, which needs `set -g set-clipboard on` in tmux. Docs should list this line. If the copy may not have reached the clipboard, the status line says so and suggests `s`.
16. **The SSH connection drops.** jtail restores the terminal and exits. Any live filter can be recreated with the command from `S`.
17. **No `/dev/tty`** (cron, or `docker run` without `-t`). With piped input and nowhere to read keys from, jtail runs in pipe mode instead of hanging.

**Finding nothing**
18. **A filter that matches nothing.** The screen reads `0 of 48,112 match level>=error svc=chekout · f edit · esc clear`, and following continues. A blank screen would look like a hang.
19. **An empty file.** The screen reads `Waiting for lines from api.log (0 bytes) · following`.

## Clutter audit and floor check

- **Borders:** nesting depth is 0. The only border is the 120+ details pane's single `│` divider.
- **Level:** two signals (the word plus color). No other state uses more than two.
- **Markers on every row:** none. Reverse video marks only the selected row, and separator rows mark only real events.
- **Chrome:** 2 of 24 rows (header and footer), and no date repeated on every line. That's about 8% of rows spent on chrome before field labels. Field labels appear only in the details view.
- **Sizes:** 80×24 shows the full list with extra fields cut off, and Enter opens full-screen details. 60 columns is the same list with seconds-only times and fewer hints. 40×6 is the stated minimum, and below it jtail says so.

## Exit codes

| Code | When |
|---|---|
| 0 | Quit, end of input in pipe mode, or the pipe closed |
| 1 | A file can't be read and `--no-wait` is set |
| 2 | Bad arguments or bad filter syntax. The message points at the problem term |
| Killed by SIGINT | `Ctrl+C` in pipe mode, so a calling shell script stops |
