```text
BUILD DASHBOARD                                      Auto-refresh: every 30s
==============================================================================
Servers: 3 responded / 5 total     Builds: 2 passed | 1 failed | 1 running
WARNING: ci-2 and ci-4 timed out. Their build status is unknown.

SERVER  BUILD         STATUS       DURATION / AGE
------------------------------------------------------------------------------
ci-1    api #412       PASSED       2m 10s
        web #88        PASSED       1m 02s

ci-2    --            UNAVAILABLE  Request timed out after 10s

ci-3  > api #413       FAILED       3m 40s

ci-4    --            UNAVAILABLE  Request timed out after 10s

ci-5    worker #9      RUNNING      Started 40s ago
------------------------------------------------------------------------------
> Selected: ci-3 / api #413
Up/Down: select   Enter: details/logs   r: refresh all   t: retry timed-out
Space: pause auto-refresh   q: quit
==============================================================================
```

The user can select a build and open its details or logs, refresh all servers, retry ci-2 and ci-4 immediately, or pause automatic polling to inspect the screen.

Timeouts indicate unavailable servers, not failed builds. The build counts cover only responding servers; any cached results should be labeled stale with their last successful update time.