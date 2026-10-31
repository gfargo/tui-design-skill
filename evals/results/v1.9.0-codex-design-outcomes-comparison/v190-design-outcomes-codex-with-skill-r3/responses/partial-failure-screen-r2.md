Show the available builds immediately, with a persistent partial-results warning. A timeout means the server’s build state is unknown.

80-column main screen:

```text
BUILD DASHBOARD                                      Auto-poll: every 30s
PARTIAL RESULTS: 3/5 servers answered; ci-2 and ci-4 timed out after 10s

Known builds: 2 passed / 1 failed / 1 running       2 servers unknown

  SERVER  BUILD        STATUS     DURATION / STARTED
> ci-1    api #412     PASSED     2m 10s
  ci-1    web #88      PASSED     1m 02s
  ci-2    --           UNKNOWN    Request timed out (10s)
  ci-3    api #413     FAILED     3m 40s
  ci-4    --           UNKNOWN    Request timed out (10s)
  ci-5    worker #9    RUNNING    Started 40s ago

j/k or Up/Down: select   Enter: details   r: refresh all
/: filter   ?: help   q: quit
```

The user can:

- Select a build and press **Enter** to inspect its details and logs.
- Select a timed-out server and press **Enter** to inspect the connection error and retry that server.
- Press **r** to poll all five servers immediately. Successful results remain visible while requests run.
- Filter by server, build, or status with **/**; **Esc** clears the filter or returns from details.
- Open help with **?**, or quit with **q** or **Ctrl+C**.

Automatic updates preserve the selected server/build and row order. If cached results exist for an unreachable server, retain them with an explicit `STALE` label and last-success time; none were supplied here. Don’t invent a next-poll countdown without knowing the polling phase.

At 80×24, everything fits in one pane. At 60 columns, shorten labels and split the footer:

```text
BUILD DASHBOARD                              Poll: 30s
PARTIAL: 3/5 answered; 2 timed out after 10s
Known: 2 passed / 1 failed / 1 running

  SERVER BUILD       STATUS   TIME
> ci-1   api #412     PASSED   2m 10s
  ci-1   web #88      PASSED   1m 02s
  ci-2   --          UNKNOWN  Timeout 10s
  ci-3   api #413     FAILED   3m 40s
  ci-4   --          UNKNOWN  Timeout 10s
  ci-5   worker #9   RUNNING  Started 40s ago

j/k Up/Down: select  Enter: details  r: refresh
/: filter  ?: help  q: quit
```

Below 60×16, show a “terminal too small” message. Clutter audit: zero borders, one text cue per status, and one selection marker; omit per-server boxes, repeated status icons, and decorative separators.