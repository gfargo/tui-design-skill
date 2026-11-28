Here's the main screen, 80 columns wide:

```
 Build Monitor                                 updated 3s ago · next poll in 27s
 2 of 5 servers not answering · 1 failed · 1 running · 2 passed
────────────────────────────────────────────────────────────────────────────────
   SERVER  JOB      BUILD   STATUS        TIME
 ▸ ci-1    api      #412    ✓ passed      2m 10s
           web      #88     ✓ passed      1m 02s
   ci-2    ⚠ NOT ANSWERING · timed out after 10s · will retry on next poll
   ci-3    api      #413    ✗ FAILED      3m 40s
   ci-4    ⚠ NOT ANSWERING · timed out after 10s · will retry on next poll
   ci-5    worker   #9      ● running     0m 40s (still going)




────────────────────────────────────────────────────────────────────────────────
 ↑↓ move   ⏎ details   l log   p poll now   f problems only   ? help   q quit
```

**Why it looks like this**

- **Servers that time out get their own state.** ci-2 and ci-4 aren't shown as empty or idle. A server that doesn't answer is a different thing from a server with no builds. If an earlier poll did get data from them, show it dimmed and labelled with its age, e.g. `api #410 ✓ passed (as of 14:01:30)`. Never show old data as if it were current.
- **The summary line is first.** It covers both kinds of problem: servers not answering and the failed build. That way you can tell if something's wrong without reading the rows.
- **Servers stay in order (ci-1 to ci-5).** Rows don't move around between polls, so people learn where to look. Pressing `f` hides everything that's fine instead.
- **Status works without colour.** Each status has its own symbol and word (✓ passed, ✗ FAILED, ● running, ⚠ not answering), so it still reads on a monochrome terminal or for colour-blind users. Colour just makes it clearer.
- **The running timer counts up between polls.** It's based on the start time, so ci-5 shows 0m 41s, 0m 42s and so on instead of jumping every 30 seconds.
- **The header shows how fresh the data is.** "updated 3s ago · next poll in 27s" shows the screen is live. If a whole poll fails, that line should turn into a warning.

**What the user can do**

| Key | Action |
|---|---|
| `↑` `↓` | Select a server or build row |
| `⏎` | Details. For a build: commit, branch, who started it, each step's duration. For an unreachable server: when it last answered, the exact error, and the last builds it reported (marked as old) |
| `l` | Open the log for the selected build. For ci-3's failed api #413, jump to the first error line |
| `p` | Poll now. Re-polls the selected server, or all servers if none is selected. Handy for checking right away if ci-2 or ci-4 is back |
| `f` | Show only problems: failed builds and servers not answering |
| `r` | Re-run the selected build. Asks for confirmation first, since it starts real work on the server |
| `?` | Full list of keys |
| `q` | Quit |

The footer only shows the keys people use most so it fits in 80 columns. `r` and the rest are listed under `?`.
