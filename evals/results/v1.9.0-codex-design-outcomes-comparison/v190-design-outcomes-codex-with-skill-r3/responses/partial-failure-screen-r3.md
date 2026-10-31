Show a partial result: keep successful responses visible and identify both timeouts. This is a full-screen dashboard with a single list and drill-down details.

80-column sketch:

```text
BUILD DASHBOARD                                      Poll interval: 30s
PARTIAL: 3/5 servers responded; ci-2 and ci-4 timed out after 10s
Reported builds: 2 passed | 1 failed | 1 running | 2 servers unknown

  SERVER  PROJECT  BUILD  STATUS    DURATION / ELAPSED
> ci-1    api      #412   passed    2m 10s
  ci-1    web      #88    passed    1m 02s
  ci-2    --       --     UNKNOWN   request timed out (10s)
  ci-3    api      #413   failed    3m 40s
  ci-4    --       --     UNKNOWN   request timed out (10s)
  ci-5    worker   #9     running   40s elapsed at response

Timeouts indicate unknown build state, not failed builds.
Automatic polling continues every 30s.

Up/Down select   Enter details   / filter   r retry timed-out servers
R refresh all   p pause display   ? help   q quit
```

The user can:

- Move between rows and press `Enter` for build details/logs, or timeout diagnostics on an unavailable server.
- Press `r` to retry ci-2 and ci-4 immediately; `R` polls all five.
- Filter by server, project, or status with `/`; `Esc` clears the filter or returns from details.
- Press `p` to freeze the display while inspecting it. Polling continues; a `PAUSED` indicator and pending-update count appear. Resume applies updates.
- Open help with `?`, or exit with `q` or `Ctrl+C`.

Refreshes preserve selection by server/project/build identity. If previous results exist for ci-2 or ci-4, retain them with `STALE` and their actual last-success age; none were supplied here.

At 60 columns, shorten the columns and wrap the key hints:

```text
BUILDS                                     Poll: 30s
PARTIAL: 3/5 responded; 2 timed out (10s)
Reported: 2 passed / 1 failed / 1 running

  SERVER BUILD         STATUS    TIME
> ci-1   api #412       passed    2m 10s
  ci-1   web #88        passed    1m 02s
  ci-2   --            UNKNOWN   timeout 10s
  ci-3   api #413       failed    3m 40s
  ci-4   --            UNKNOWN   timeout 10s
  ci-5   worker #9     running   elapsed 40s

Up/Down select  Enter details  / filter
r retry timeouts  R refresh all  p pause
? help  q quit
```

Both fit at 24 rows. Below the declared minimum of 60×16, show the required size and retain quit controls. Clutter audit: zero borders, one selection marker, one text label per row state, and no redundant icons or per-server panels.