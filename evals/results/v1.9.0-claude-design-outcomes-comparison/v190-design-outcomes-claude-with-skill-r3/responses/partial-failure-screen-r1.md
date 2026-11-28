I've read the skill's guidance on layout, empty/error/partial states and key bindings, and here's the design.

This is a single list of builds with the poll status in the header. Enter opens details. The two servers that didn't answer stay in the list as rows, in their usual place. Nothing gets blanked or hidden.

## Main screen, 80×24

```
 CI builds ⋅ 3 of 5 servers answered                 polled 0s ago ⋅ next in 30s

 SERVER  PIPELINE   RUN  STATUS   DURATION
 ci-1    api       #412  passed     2m 10s
         web        #88  passed     1m 02s
 ci-2    no response, timed out after 10s
>ci-3    api       #413  FAILED     3m 40s
 ci-4    no response, timed out after 10s
 ci-5    worker      #9  running       40s
















 enter details ⋅ l log ⋅ R rerun ⋅ r poll now ⋅ p pause ⋅ q quit ⋅ ? help
```

How to read it:

- **`>` is the selected row.** In the real app the whole row is shown in reverse video and there's no `>`. On launch, the cursor starts on the first row that needs attention, which is the ci-3 failure. After that it stays on the same build across refreshes, even when rows above it change.
- **Status uses a word, plus at most one color.** `FAILED` is red and `running` is yellow. `no response` is yellow. `passed` is plain text, because the rows that need you should stand out, not the ones that are fine. Every status is still readable with `NO_COLOR` or on a monochrome terminal.
- **Rows stay in server order (ci-1 to ci-5).** They don't re-sort by status on each poll, so every server is always in the same spot. With only five servers, the failure is easy to spot without moving it to the top.
- **ci-2 and ci-4 say what happened**: "timed out after 10s". The header gives the count ("3 of 5 servers answered"). There's no popup every 30 seconds.
- **ci-5's time counts up every second** between polls (40s, 41s, …), so it doesn't freeze for 30 seconds and then jump.
- **Repeated server names are left blank** (the second ci-1 row), so each server's builds read as a group.
- **The second-to-last row is a status line, blank when idle.** It shows short messages like `✓ ci-2 answered on retry` or `✗ Rerun failed: ci-3 returned 503`. Errors stay until you dismiss them.

## What the user can do

| Key | Action |
|---|---|
| `↑`/`↓`, `j`/`k` | Move the selection |
| `Enter` | Details for the selected row. For a build: steps, commit, who triggered it, and the end of the log. For ci-2 or ci-4: the error, when the server last answered, and how many polls in a row it has missed |
| `l` | Full log. For ci-5 it follows new output live; scrolling up pauses that and shows `▾ 12 new` |
| `R` | Rerun the selected build (ci-3). It's on capital R so it's not one slip away from `r` |
| `c` | Cancel a running build (ci-5) after a confirmation: `Cancel worker #9 on ci-5? [y/N]`, default No |
| `r` | Poll now. On an unreachable row the hint changes to `r retry ci-2` |
| `p` | Pause updates. The header shows `PAUSED ⋅ 2 changes waiting`, and they're applied when you resume |
| `o` / `y` | Open the build in the browser / copy its URL |
| `/` | Filter, e.g. `failed` or `ci-5`. Not worth a spot in the footer with only six rows |
| `Esc` | Goes back one step: closes details, clears a filter or cancels a poll in progress. It never quits |
| `q`, `Ctrl+C` | Quit, with no confirmation (quitting a viewer loses nothing) |
| `?` | Full list of keys |

The footer changes with the selected row: `R rerun` shows on the failed build, `c cancel` on the running one and `r retry ci-2` on a dead server.

## Other states of the same screen

```
Poll in progress    CI builds ⋅ polling… 4s          (old rows stay, Esc cancels)
Server had answered ci-2    api  #410  passed  1m 55s   STALE 30s   (row dimmed)
  before                    — last data it sent, kept with its age
All 5 time out      ✗ No servers answered (timed out after 10s) ⋅ r retry
                      (last-known rows stay visible, dimmed and marked STALE)
```

## At 60 columns (a tmux split)

The table is 42 columns wide, so it doesn't change. Only the header and footer get shorter:

```
 CI builds ⋅ 3 of 5 answered                     next in 30s

 SERVER  PIPELINE   RUN  STATUS   DURATION
 ci-1    api       #412  passed     2m 10s
 ...
 enter details ⋅ R rerun ⋅ r poll now ⋅ q quit ⋅ ? help
```

Below about 44×10, the app shows `terminal too small: need 44x10` instead of a broken layout, and `q` still works.

## Clutter check

- **Borders:** none. The terminal edge already frames the screen, and blank rows separate the sections.
- **Status signals:** at most two per status (a word plus a color). Passed builds get one.
- **Markers:** only the selected row has one.
- **Chrome:** about 3 of 24 rows: the title, column headings and footer.
