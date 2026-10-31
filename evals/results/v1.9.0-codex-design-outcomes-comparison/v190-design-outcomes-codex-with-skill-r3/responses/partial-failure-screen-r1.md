Use a single full-screen table. Keep successful responses visible and mark the result **PARTIAL**: a timeout means that server’s build state is unknown.

80-column screen (unused space remains blank):

```text
BUILD DASHBOARD                         Poll interval: 30s
PARTIAL: 3/5 servers responded; 2 timed out

  SERVER  BUILD         STATUS       DURATION / AGE
> ci-1    api #412      PASSED       2m 10s
  ci-1    web #88       PASSED       1m 02s
  ci-2    --            UNKNOWN      Request timed out after 10s
  ci-3    api #413      FAILED       3m 40s
  ci-4    --            UNKNOWN      Request timed out after 10s
  ci-5    worker #9     RUNNING      Started 40s ago

Reported builds: 2 passed, 1 failed, 1 running
ci-2 and ci-4 build states unavailable.

Up/Down select  Enter details  r retry timeouts  R refresh all
Space pause updates  / filter  ? help  q quit
```

The user can:

- Select a build and press `Enter` for details and available logs. On a timeout row, `Enter` shows connection diagnostics.
- Press `r` to retry ci-2 and ci-4 immediately, or `R` to poll all five. Existing results stay visible during requests.
- Pause display updates with `Space`; show `PAUSED` and the age of displayed data until resumed. Refreshes preserve selection by server and build ID.
- Filter by server, project, or status with `/`. `Esc` clears the filter or returns from details; `q` quits from the main screen.

No prior results were supplied for ci-2 or ci-4. If cached results exist, retain them with `STALE` and their last-success age. Summary counts must identify them separately. The next-poll countdown should use the actual scheduler deadline.

At 60 columns, shorten headings and timeout wording:

```text
BUILD DASHBOARD                         Poll: 30s
PARTIAL: 3/5 responded; 2 timed out

  SERVER BUILD        STATUS   TIME
> ci-1   api #412      PASSED   2m 10s
  ci-1   web #88       PASSED   1m 02s
  ci-2   --            UNKNOWN Timeout (10s)
  ci-3   api #413      FAILED   3m 40s
  ci-4   --            UNKNOWN Timeout (10s)
  ci-5   worker #9     RUNNING Started 40s ago

Reported: 2 passed, 1 failed, 1 running
Up/Down select  Enter details  r retry timeouts
R refresh  Space pause  / filter  ? help  q quit
```

Both fit at 24 rows. Below 60 columns, move timing into details; below 48×12, show the required size and quit keys. Clutter audit: zero borders, one selection marker, and one text label per status; remove per-server boxes, repeated “server” labels, and decorative status icons.