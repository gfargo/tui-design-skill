I don’t see any screens attached or files in the workspace, so I can’t review the layouts yet. For a dashboard fetching from five CI servers, **partial success should be a normal state**: one unreachable server shouldn’t hide the other four.

Design these states:

| State | What the TUI should show |
|---|---|
| **Initial load** | Five server rows immediately, each marked “Connecting…”; keep navigation and quit available. |
| **Partial load** | Results appear per server as they arrive. Distinguish waiting from failed. |
| **Refreshing** | Keep existing results visible, with a subtle refresh indicator. |
| **Stale data** | Last known status plus “Last updated 8m ago.” Failed refreshes must never look current. |
| **One or more servers unavailable** | Inline timeout, connection, or server error; retry the affected source. |
| **All servers unavailable** | A clear overall failure, last known results if available, and retry/configuration shortcuts. |
| **Authentication or permission failure** | Identify the affected server and the corrective action; distinguish expired credentials from denied access. |
| **Rate limited** | Show when the next retry is allowed; avoid a retry loop. |
| **Empty results** | Distinguish “No builds yet,” “No matching builds,” and “Server not configured.” Offer the relevant next step. |
| **Unexpected or incomplete response** | Mark missing status as “Unknown,” preserve usable results, and expose diagnostic details. |
| **Build lifecycle** | Queued, running, passed, failed, canceled, skipped, and unknown. Include blocked/manual approval if supported. |
| **Cross-server disagreement** | Show branch, commit, and build identity so results from different revisions cannot imply release readiness. |
| **Terminal constraints** | A usable narrow layout, explicit minimum-size message, scrolling, and selection preserved during updates. |

The most important rule: **build status and connection status are separate**. “Build failed,” “fetch failed,” and “last known build passed” need visibly different treatments, using text or symbols as well as color.

If the TUI also triggers releases, add confirmation with the exact version/commit and targets, submitting, accepted/in progress, succeeded, failed, and partial completion. A timeout after submission needs **“Outcome unknown—checking”** rather than an immediate retry that could duplicate the release.

Start by mocking four screens: **mixed loading/results, one server failing with stale data, all servers unavailable, and conflicting commit versions across servers**. Those will expose most of the structural gaps in a happy-path design.