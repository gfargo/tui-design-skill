I'd make this one flat table with a row for every build, sorted by server. A server that timed out still gets its own row saying it didn't answer. It shouldn't be hidden, shown as "no builds", or called "down". Three of five servers answered, so the screen should say that plainly.

## Main screen at 80×24

```
 CI builds                                    updated just now · next poll in 30s
 1 failed · 1 running · 2 passed · 2 of 5 servers not responding

 SERVER  JOB     RUN    STATUS                       TIME
 ci-1    api     #412   passed                     2m 10s
         web     #88    passed                     1m 02s
 ci-2    no response · timed out after 10s
>ci-3    api     #413   failed                     3m 40s
 ci-4    no response · timed out after 10s
 ci-5    worker  #9     running                    0m 40s








 ↑↓ move ⋅ enter details ⋅ l log ⋅ r re-poll ⋅ R poll all ⋅ / filter ⋅ ? help
```

The `>` only shows where the selection is. On screen, the ci-3 row is drawn in reverse video with no marker glyph.

**How each line works:**
- **Header:** "updated just now" counts up every second (5s ago, 10s ago…). "next poll in 30s" counts down. If a poll is in progress, it says "polling…" so users always know how fresh the data is.
- **Summary line:** Counts are worded so they still read under `NO_COLOR`. Failures come first. "2 of 5 servers not responding" marks a partial result instead of passing it off as complete.
- **Status column:** Each status has one word and at most one color: `failed` red, `no response` yellow, `running` cyan, `passed` plain. Plain passes keep the problems easy to spot. There are no ✓/✗ glyphs, because word plus color is already two cues.
- **Timed-out rows** say exactly what happened ("timed out after 10s"). They don't guess why. If ci-2 answered an earlier poll, its last-known builds appear dimmed under that row, marked `STALE 30s`. They are never shown as current. I haven't drawn that here because your snapshot doesn't include earlier data.
- **Running row:** The elapsed time counts up locally from the start time the server reported. The next poll replaces it with the final result. There's no spinner, since the ticking clock already shows it's live.
- **Server name** appears only on the first row of each group (ci-1's second build leaves it blank). That cuts repetition without losing grouping.
- **Row order** stays by server and doesn't change between polls. The failure is found through the summary line and the initial selection. If failures were moved to the top, rows would jump under the cursor.

## What the user can do

| Key | Action |
|---|---|
| `↑`/`↓`, `j`/`k` | Move the selection. It follows the build by ID across polls, not by row number. |
| `Enter` | Open details for the selected build: steps, duration, commit. On a no-response row it shows poll diagnostics instead: endpoint, last successful poll, consecutive misses, the error. |
| `l` | Open the selected build's log. On ci-5 it follows live output. Scrolling up pauses following; `G` resumes. |
| `r` | Poll the selected server now instead of waiting up to 30s. Useful for ci-2/ci-4. |
| `R` | Poll all five servers now. |
| `/` | Filter, e.g. `failed`, `ci-3`, `api`. Shows a count like `1/6`. `Esc` clears it. |
| `p` | Pause updates. The header shows `PAUSED · 2 changes pending`; `p` again applies them. |
| `?` | Full key list. |
| `q` / `Ctrl+C` | Quit. No confirmation, since the dashboard only reads and quitting loses nothing. |

When the dashboard opens, the selection starts on the first failed build (ci-3 api #413), so `Enter` or `l` gets to the problem in one key. If your CI API lets the dashboard rerun builds, put that on its own key with a `y/N` confirm (default No). It's the only action here that changes anything on the servers.

## At 60 columns (tmux split)

```
 CI builds                    updated just now · next 30s
 1 failed · 1 running · 2 passed · 2/5 not responding

 SERVER  JOB          STATUS                  TIME
 ci-1    api #412     passed                2m 10s
         web #88      passed                1m 02s
 ci-2    no response (timeout 10s)
>ci-3    api #413     failed                3m 40s
 ci-4    no response (timeout 10s)
 ci-5    worker #9    running               0m 40s

 enter details ⋅ l log ⋅ r re-poll ⋅ / filter ⋅ ? help
```

At this width, the job and run number share one column and the timeout text gets shorter. The footer drops hints starting with the least-used, but always keeps `?`. Below about 44×10 the screen just says `terminal too small: need 44x10`, and `q` still works.

## Clutter check

- No borders; whitespace and the header row separate everything.
- Each status uses one word and at most one color. Passes have no color.
- No marker appears on every row. The only highlight is the reverse-video selection.
- Most of the screen is build data; the only chrome is the header, the summary line, and the footer.

One implementation note: poll the five servers in parallel, each with its own 10s timeout. That way two silent servers don't hold back the other three, which is what lets this screen show partial results honestly.
