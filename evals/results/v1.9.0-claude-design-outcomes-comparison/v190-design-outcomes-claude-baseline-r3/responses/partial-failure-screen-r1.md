```
 BUILD MONITOR                                 updated 14:32:00 · next poll in 28s
 5 servers: 3 responding, 2 unreachable   Builds: 1 failed, 1 running, 2 passed
────────────────────────────────────────────────────────────────────────────────
 ci-1  ● online
         ✓ api      #412   passed     2m 10s
         ✓ web      #88    passed     1m 02s

 ci-2  ○ NO RESPONSE — timed out after 10s        last seen 14:31:30 (30s ago)
         builds unknown

 ci-3  ● online
       ▸ ✗ api      #413   FAILED     3m 40s

 ci-4  ○ NO RESPONSE — timed out after 10s        last seen 14:31:30 (30s ago)
         builds unknown

 ci-5  ● online
         ◷ worker   #9     running    0m 40s so far





────────────────────────────────────────────────────────────────────────────────
 ↑↓ select  enter details  l log  r retry now  f failures  p pause  q quit
```

**Design choices**

- **The two summary lines count servers and builds separately.** "1 failed" and "2 unreachable" are different problems. A build failure means the code is broken. A timeout means you can't see that server's builds at all.
- **Timed-out servers stay on screen and get a full row.** If ci-2 and ci-4 just disappeared, the screen would look like everything is fine. Their rows also say "builds unknown" and don't show leftover results. If the dashboard keeps the last successful response, I'd show those builds dimmed and labelled "as of 14:31:30" so they aren't mistaken for live data. The "last seen" time in the sketch is an example value.
- **Servers stay in the order ci-1 to ci-5.** Re-sorting by severity every 30 seconds would move rows around while you're reading them. Color does the highlighting instead: red for FAILED and NO RESPONSE, yellow for running, plain or green for passed.
- **The cursor starts on the failed build**, since that's the item most likely to need action.
- **The running build's elapsed time counts up every second on the client.** Without that, it would freeze for 30 seconds between polls and look stuck.
- **"Next poll in 28s"** shows that the data is live and how old it is.

**What the user can do**

| Key | Action |
|---|---|
| ↑ / ↓ | Move between builds and server rows |
| enter | On a build: open details (commit, author, steps, which step failed). On an unreachable server: show the error, the time of its last successful reply, and recent poll history |
| l | Open the log for the selected build, starting at the failure for failed builds or following live output for running ones |
| r | Poll now instead of waiting. On an unreachable server, retry only that server |
| f | Show only problems (failed builds and unreachable servers). Press again to show everything |
| p | Pause or resume polling so the screen stops changing while you read. The header shows "PAUSED" |
| q | Quit |
| ? | Full key help (not in the footer, to keep it within 80 columns) |

I left out actions that trigger builds, like re-running a failed one. Those change things on the servers, so if you want them, they should ask for confirmation before running.
