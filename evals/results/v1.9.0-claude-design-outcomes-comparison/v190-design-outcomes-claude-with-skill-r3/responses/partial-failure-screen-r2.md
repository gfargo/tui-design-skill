I'd make this a full-screen table with **one row per build and one row per server that didn't answer**. A summary line goes on top and the shortcut keys go at the bottom. ci-2 and ci-4 should never disappear, and the timeouts shouldn't blank the rest of the screen: the three servers that answered still show their results.

## Main screen at 80×24 (rows 11–22 are empty)

```
 ci-dash                                      updated 2s ago ⋅ next poll in 28s
 1 failed ⋅ 1 running ⋅ 2 passed ⋅ 2 servers not answering

 SERVER  JOB     BUILD  STATUS     DURATION
 ci-1    api      #412  passed       2m 10s
         web       #88  passed       1m 02s
 ci-2                   no answer            timed out after 10s
 ci-3    api      #413  failed       3m 40s
 ci-4                   no answer            timed out after 10s
 ci-5    worker     #9  running      0m 40s












 q quit ⋅ enter details ⋅ l log ⋅ r poll now ⋅ / filter ⋅ p pause ⋅ ? help
```

**How each part behaves:**

- **Selected row:** The selected row is shown in reverse video. At launch the cursor goes to the first problem row (ci-2). After that it follows the build or server itself, not a line number, so the next poll doesn't move it.
- **Status colours:** Each status gets a word and at most one colour. `failed` is red, `no answer` is yellow, `running` is the accent colour, and `passed` stays plain so problems stand out. With colour turned off (`NO_COLOR`) or on a monochrome screen, the words still carry the meaning.
- **ci-2 and ci-4:** Each gets a row in its usual spot, not a banner. The server order stays ci-1 to ci-5 and never re-sorts, so people learn where each server is.
  - **If an earlier poll did get data from them:** keep those old build rows under the server row, dimmed and marked `STALE 1m`, instead of throwing them away. Your example doesn't include earlier data, so the sketch shows none.
- **The running build:** The `0m 40s` keeps counting up every second between polls. It's measured from the start time the server reported, so it doesn't jump when the next poll arrives.
- **Top-right corner:** `next poll in 28s` counts down. During a poll it changes to `polling… 3s`, and the old rows stay on screen until new data replaces them.
- **Empty status line:** The line above the footer stays blank when nothing is happening. It only shows messages like `✓ ci-2 answered` or `✗ ci-4 still not answering`.

## Same screen in a 60-column tmux split

```
 ci-dash                       updated 2s ago ⋅ next in 28s
 1 failed ⋅ 1 running ⋅ 2 passed ⋅ 2 not answering

 SERVER  JOB     BUILD  STATUS     DURATION
 ci-1    api      #412  passed       2m 10s
         web       #88  passed       1m 02s
 ci-2                   no answer            timeout 10s
 ci-3    api      #413  failed       3m 40s
 ci-4                   no answer            timeout 10s
 ci-5    worker     #9  running      0m 40s

 q quit ⋅ enter details ⋅ l log ⋅ r poll now ⋅ ? help
```

The table only needs 44 columns, so it fits as it is. Only the notes and the footer get shorter. As the window narrows further, columns drop in this order: the note, then BUILD, then DURATION. Below 30×8 the screen shows `terminal too small: need 30x8 (q quits)` instead of a broken layout.

## What the user can do

| Key | Action |
|---|---|
| `↑`/`↓` or `j`/`k` | Move between rows. The ci-2 and ci-4 rows can be selected too. |
| `Enter` | **On a build:** commit, branch, steps, the step that failed (ci-3), and the last lines of the log. **On a server that didn't answer:** when it last answered, the error, how many polls in a row failed, and what its last response contained. `Esc` returns to the list. |
| `l` | Open the build log. For a running build (ci-5) it follows new output as it arrives; scrolling up pauses that, and `G` jumps back to the end. |
| `r` | Poll all five servers now instead of waiting for the countdown. While a server is being retried, its row shows `retrying… 4s`. |
| `/` | Filter rows by server, job, or status (for example `failed` or `no answer`). `Esc` clears the filter. |
| `p` | Pause updates. The header shows `PAUSED ⋅ 3 changes waiting`, rows stop changing, and pressing `p` again applies the waiting changes. |
| `o` | Open the selected build in the CI system's web page, if it has one. |
| `?` | Show every key, grouped by screen. |
| `q` / `Ctrl+C` | Quit right away with no prompt, since quitting loses nothing. |

If the CI system lets you start builds again, `R` (re-run ci-3's api #413) could be added. It does something on the server, so it should ask first: `Re-run api #413 on ci-3? [y/N]`, defaulting to No.

## Why it looks this way (counting the clutter)

- **No boxes:** There are no borders at all. The edge of the terminal and blank lines do the separating.
- **Two signals at most per status:** For example, the word `failed` plus red. There are no extra icons like ✓ or ✗ on rows. Passing rows get no highlight at all.
- **Markers only on exceptions:** Nothing is repeated on every row. The note column only appears on the two servers that timed out, and "ci-1" isn't repeated on its second build.
- **Little space spent on labels:** Only the one column-header line, the app name, and the footer aren't data.

For scripts and screen readers, add `ci-dash --once --json`, plus a plain mode that prints the same rows as simple lines, such as `ci-2 no answer (timed out after 10s)`.
