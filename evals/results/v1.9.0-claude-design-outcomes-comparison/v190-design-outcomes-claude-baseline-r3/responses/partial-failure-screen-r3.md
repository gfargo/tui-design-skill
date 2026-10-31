```
 CI Builds                                        polled just now · next in 30s
 ──────────────────────────────────────────────────────────────────────────────
 1 failed · 1 running · 2 passed · 2 of 5 servers not responding

   SERVER  JOB      BUILD  STATUS        TIME
   ci-1    api      #412   ✓ passed      2m 10s
   ci-1    web      #88    ✓ passed      1m 02s
   ci-2    ? not responding · timed out after 10s · retry in 30s
 > ci-3    api      #413   ✗ FAILED      3m 40s
   ci-4    ? not responding · timed out after 10s · retry in 30s
   ci-5    worker   #9     ● running     40s so far




 ──────────────────────────────────────────────────────────────────────────────
 ↑↓ select  enter details  r poll now  f failures only  o open  ? help  q quit
```

**Why it looks this way**

- **The summary line answers "is anything wrong?"** before you read any rows. The failure comes first, and the unreachable servers are counted separately from the builds. A silent server isn't a passing server, and it isn't a failing build either.
- **Rows stay in server order (ci-1 to ci-5).** The screen refreshes every 30 seconds, so sorting by status would make rows move around while you're reading them. The cursor starts on the failed build instead, and the failure stands out through red, bold, the ✗ symbol and the uppercase word. Every status has a symbol and a word, so the screen still works without color.
- **Silent servers show only what's actually known.** For ci-2 and ci-4 we know they timed out after 10 s and when the next try is, and nothing else. The screen doesn't fill in made-up job rows. If an earlier poll had returned results, those would appear dimmed and marked "as of 12:03:30" so old data can't pass for current data.
- **The running build's timer counts up between polls** ("40s so far", then "41s so far"…) so it doesn't look stuck. A real update replaces it on the next poll.
- **The header shows how fresh the data is** ("polled just now · next in 30s"). If a whole poll fails or runs late, this is where it shows.

**What the user can do**

| Key | Action |
|---|---|
| `↑` `↓` | Move the selection between rows |
| `enter` | Open details for the selected row. For a build: the failing step, the last lines of the log, the commit and who triggered it. For a silent server: the error, when it last answered, and recent poll results (one timeout vs. down for an hour) |
| `r` | Poll all servers now instead of waiting for the 30-second cycle |
| `f` | Show only rows that need attention (failed, not responding) and hide passed builds. Press again to show everything |
| `o` | Open the selected build or server in the CI system's web UI |
| `?` | Show the full list of keys |
| `q` | Quit |

The dashboard only watches, so there are no actions like re-running a build. If those get added later, they should ask for confirmation first, because they change things on the CI servers.
