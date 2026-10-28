Design for **five independently updating sources**. The highest-risk state is “four servers show passing builds; the fifth is unavailable.” That must never look like an all-clear.

I used the requested `tui-design` skill. No screens or project files were available in the workspace, so this is a state review based on your description.

Keep three things distinct:

- **Build outcome:** queued, running, passed, failed, canceled, skipped, unknown.
- **Server connection:** connecting, reachable, timed out, disconnected, authentication required, rate limited.
- **Data freshness:** never loaded, current, refreshing, stale.

A server can be disconnected while its last-known build result is “passed.”

| State to design | What the screen should say and do |
|---|---|
| **Initial / unconfigured** | “No CI servers configured.” Offer a concrete setup action. Invalid configuration should identify the affected server. |
| **First load** | Render the dashboard immediately with all five server slots. Show responses independently: “3/5 responded; 2 connecting.” Never wait for the slowest server to display results. |
| **Refreshing** | Keep existing rows visible. Show which sources are refreshing; preserve selection and scroll position. |
| **Partial results** | “4/5 current; ci-east timed out.” Keep healthy results usable and offer retry for the affected server. |
| **Stale / disconnected** | Keep cached results, visibly labeled “Last known: PASSED · updated 8m ago.” Show reconnect progress and the next retry time. With no cache, show “UNKNOWN — no successful fetch.” |
| **All sources unavailable** | Persistent summary: “0/5 reachable.” Retain cached results with ages, or show recovery instructions if none exist. Keep retry, details, and quit available. |
| **Authentication / permission failure** | Identify the server and distinguish expired credentials from denied access. Offer the relevant credential/configuration route; repeated automatic retries won’t fix access. |
| **Rate limited / server error / invalid response** | Show the specific cause. Respect retry timing for rate limits. An unsupported response must produce “status unknown,” never “no builds” or “passed.” |
| **Empty** | Distinguish “No builds for release v2.4,” “No matching filters,” and “This server has no projects.” Offer change-release, clear-filter, or configuration actions respectively. |
| **Mixed build outcomes** | Support queued, running, failed, canceled, skipped, and unknown alongside passed. Skipped or missing required checks must not silently count as success. |
| **Details / logs unavailable** | Keep the build summary visible when log retrieval fails. Retry logs locally without replacing the dashboard with a global error. |
| **Paused / recovered** | Label paused updates explicitly; data continues aging. On recovery, update the affected source without stealing focus and briefly report “ci-east reconnected.” |
| **Terminal too small** | Show the required dimensions and retain quit controls. Restore the current view after resizing. |

**Make the release summary conservative.** Show build results and coverage separately: `3 passed · 1 failed · 1 unknown | 4/5 current`. Only show “ready” when every required check for the selected release/commit is current and satisfies your release policy. Five green builds from different commits don’t establish readiness.

A proposed layout, with the same degraded state at wide and narrow widths:

```text
Wide, 120+ columns                         Narrow, 60 columns
Release v2.4 / a1b2c3                      Release v2.4 / a1b2c3
NOT READY | 4/5 current                    NOT READY | 4/5 current

SERVER   BUILD    FETCH       AGE          SERVER   BUILD    DATA
> ci-1   PASSED   current      8s          > ci-1   PASSED   current
  ci-2   FAILED   current     12s            ci-2   FAILED   current
  ci-3   RUNNING  current      4s            ci-3   RUNNING  current
  ci-4   PASSED   timeout     8m            ci-4   PASSED   STALE 8m
  ci-5   QUEUED   current      9s            ci-5   QUEUED   current

Selected server details alongside         Enter: details for selected server
r retry server  R refresh all              r retry  R refresh  Enter details
/ filter  ? help  q quit                   / filter  ? help  q quit
```

At **80×24**, use the full-width list and open details with Enter. At **60 columns**, hide secondary metadata before hiding freshness or failure information; truncate long names and reveal them in details. A proposed minimum is **60×12**, to validate with rendered frames; below it, show the too-small message.

For clutter, I can’t count your existing borders or markers without screens. In this proposal: border depth is **0**, selection uses one marker, and status uses text with optional color. Avoid five nested server cards, repeated “Build status:” labels, or green-plus-checkmark-plus-`PASS` on every row. Spend that space on source coverage and data age.

Start verification with **4 healthy + 1 timeout**, **cached pass becoming stale**, **all five unavailable**, **wrong-commit results**, and **recovery while inspecting a row**. Those expose the most consequential gaps in a happy-path dashboard.