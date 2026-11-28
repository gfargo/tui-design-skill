```text
BUILD DASHBOARD                                     Auto-refresh: every 30s
===============================================================================
Servers: 3 responded / 5                          2 timed out (10s limit)
Builds reported: 2 passed | 1 failed | 1 running

SERVER  PROJECT  BUILD   STATUS     DURATION / AGE
-------------------------------------------------------------------------------
ci-1    api      #412    PASSED     2m 10s
        web      #88     PASSED     1m 02s
ci-2    --       --      TIMEOUT    No current build data
> ci-3  api      #413    FAILED     3m 40s
ci-4    --       --      TIMEOUT    No current build data
ci-5    worker   #9      RUNNING    Started 40s ago
-------------------------------------------------------------------------------
Partial results: ci-2 and ci-4 did not answer. Their build status is unknown.

Up/Down Select   Enter Details   r Refresh all   t Retry timed-out servers
Space Pause auto-refresh   q Quit
===============================================================================
```

The user can select a build and open its details, starting with the failed
build selected here. They can refresh all servers, retry only ci-2 and ci-4,
or pause automatic polling to inspect the screen. Timeouts remain distinct
from failed builds; unavailable servers do not count as passing or failing.