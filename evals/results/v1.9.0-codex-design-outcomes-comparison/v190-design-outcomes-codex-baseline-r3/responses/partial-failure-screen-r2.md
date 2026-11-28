```text
BUILD DASHBOARD                                      Auto-refresh: every 30s
===============================================================================
PARTIAL RESULTS: 3 of 5 servers answered. 2 timed out after 10s.
Build totals below exclude servers that did not answer.

SERVER  CONNECTION   PROJECT  BUILD   RESULT    DURATION / AGE
-------------------------------------------------------------------------------
ci-1    Responded    api      #412    PASSED    2m 10s
                     web      #88     PASSED    1m 02s
ci-2    TIMED OUT    Unknown build status; server did not answer
ci-3    Responded    api      #413    FAILED    3m 40s
ci-4    TIMED OUT    Unknown build status; server did not answer
ci-5    Responded    worker   #9      RUNNING   Started 40s ago*
-------------------------------------------------------------------------------
Reported builds: 2 passed | 1 failed | 1 running
* Age reported at last response.

Up/Down Select   Enter Details   R Refresh all   T Retry timed-out servers
Space Pause auto-refresh   Q Quit
===============================================================================
```

The user can select a build and open its details or logs, including the failed `api #413`. Selecting a timed-out server opens connection details; its builds remain unknown.

They can refresh all servers, retry only ci-2 and ci-4, or pause automatic polling to inspect results. Keep current results visible during retries, and label any retained older results as stale.