I don’t see screenshots or screen files attached, so I can’t review the layouts directly. For a dashboard polling five CI servers, the key is to model **build status and data freshness separately**: “last build passed” doesn’t mean “currently verified.”

These are the states I’d design:

| State | What the screen should show |
|---|---|
| Initial loading | Five server rows immediately; mark each pending and show progress such as “3/5 checked.” |
| Refreshing | Keep existing results visible, with a refresh indicator. Preserve selection and scroll position. |
| Partial availability | Show working servers normally; put errors on affected rows. Summarize “4/5 reachable.” |
| All servers unavailable | A dashboard-level explanation, last successful update, and retry action. Retain cached results if available. |
| Stale results | Label cached status explicitly: “Passed · last checked 12m ago.” Show freshness per server. |
| Connection errors | Distinguish timeout, DNS/network failure, and server error; show retry timing and allow manual retry. |
| Authentication/configuration errors | Identify expired credentials, forbidden access, or an invalid endpoint, with a useful recovery action. Never expose tokens. |
| Rate limited | Show when polling will resume; avoid endless retry spinners. |
| No builds | Distinguish no build history, no build for this commit, and no matches for the current filter. |
| Build lifecycle | Queued, running, waiting for approval, passed, failed, canceled, skipped, and unknown/unrecognized status. |
| Inconsistent results | Flag different commits, branches, artifacts, or environments across servers. Five green builds may refer to different releases. |
| Detail/log failure | Keep the dashboard usable if a selected build’s details or logs fail to load. |
| Terminal constraints | A usable narrow layout, “terminal too small” fallback, truncated text with accessible details, and status symbols that work without color. |

**Release readiness deserves its own summary.** Distinguish “ready,” “blocked by failed builds,” “checks pending,” and “cannot verify.” Missing or stale required checks must not silently count as passed. Make required versus optional servers explicit.

If the TUI can trigger releases, reruns, or cancellations, also design confirmation, submitting, success, rejected, partial success, and **outcome unknown** states. A timed-out request may already have started the action; offer reconciliation before retrying.

For the next design pass, prioritize these five screens:

1. Cold start with servers responding at different speeds.
2. Four healthy servers and one timeout with cached data.
3. All servers unreachable.
4. All builds green, but one is for the wrong commit.
5. A narrow terminal showing a long error while a row is selected.

Attach the screens and I can map these states to your actual layouts and key bindings.