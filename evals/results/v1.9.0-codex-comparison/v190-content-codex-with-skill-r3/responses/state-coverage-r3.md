**Prioritize partial failure and stale data.** With five CI servers, the dangerous screen is one that looks healthy while a required server hasn’t reported.

I used the `tui-design` skill. No screens or source files were available in this workspace, so this is a state review based on your description.

**Model build status separately from data availability.** A build can be `PASSED` while its last observation is `STALE`. “Server unreachable” must never become “build failed,” “no builds,” or an implied pass.

| State to design | What the screen should say or preserve | Recovery |
|---|---|---|
| First launch / missing configuration | “No CI servers configured” or identify invalid server settings | Show how to configure them |
| Initial loading | Render all five server rows immediately; mark each `Loading`, with elapsed time for slow requests | Cancel fetch; quit remains available |
| Partial results, still loading | Show completed results immediately: “3/5 responded; 2 loading” | Inspect available builds |
| Partial failure | Keep successful servers visible; identify each unavailable source and its reason | Retry selected server |
| Refreshing | Keep existing rows and timestamps; mark requests in flight | Avoid duplicate refresh requests |
| Stale / disconnected | Preserve last-known results with `STALE`, last successful fetch time, and retry timing | Retry now; inspect error |
| All servers unavailable | Distinguish “no observations yet” from “cached results available” | Retry all; inspect connection details |
| Authentication / permission error | “CI-4: credentials expired” or “access denied” | Explain which credentials or permissions need attention |
| Rate limit / server error | Identify affected server; show next retry or `Retry-After` | Back off automatically; avoid retry storms |
| Empty source | “No builds for release v2.4 on CI-2” | Change release/branch or inspect server |
| Filter has no matches | Show active filter and unfiltered count | Clear filter |
| Incomplete / unexpected response | Preserve valid results; mark affected fields `Unknown` or `Unsupported` | Inspect details; retry if appropriate |
| Recovery | Replace stale data only after a successful fetch; briefly report “CI-3 reconnected” | Preserve selection and scroll position |
| Terminal too small | State required dimensions | Resize; keep quit working |

Also cover the build lifecycle: **not started, queued, running, passed, failed, canceled, skipped, and unknown**. Expose blocking/manual approval when your CI providers support it. A missing required build is different from a deliberately skipped optional build.

For the release summary, use an explicit rule:

- **Ready:** every required check passed, observations meet your freshness policy, and all results belong to the intended release/commit.
- **Blocked:** a known required check failed or otherwise blocks release.
- **Pending:** required checks are queued or running.
- **Unknown:** required evidence is missing, stale, inaccessible, or belongs to another commit.

Keep coverage visible alongside the verdict. For example: `BLOCKED · 1 failed · 1 server unavailable`. A known failure must remain visible even when other evidence is missing.

A proposed wide view and its 60-column fallback:

```text
Wide
Release v2.4 / a81c9d   UNKNOWN   Fresh sources 3/5
SERVER   BUILD       DATA          DETAIL
> CI-1   Passed      Fresh         a81c9d
  CI-2   Running     Fresh         4m elapsed
  CI-3   Passed      STALE 8m      Timeout; retry in 20s
  CI-4   Unknown     Unavailable   Credentials expired
  CI-5   Queued      Fresh         Waiting for runner

Enter details   r retry selected   R refresh all   ? help   q quit
```

```text
60 columns
v2.4 / a81c9d   UNKNOWN   Fresh 3/5
SERVER  BUILD    DATA
> CI-1  Passed   Fresh
  CI-2  Running  Fresh
  CI-3  Passed   STALE 8m
  CI-4  Unknown Unavailable
  CI-5  Queued  Fresh

Enter details  r retry  R refresh  ? help  q quit
```

At **80×24**, retain the unified table and move verbose errors into details. At **60 columns**, hide inline detail and use a full-screen detail view with `Esc` to return. A proposed minimum is **60×12**; below that, show the too-small state.

For clutter, I can’t count your existing borders without the screens. In the proposed layout: **zero nested borders, one textual status per dimension, and one selection marker**. Avoid five boxed server panels, repeated “Build status:” labels, and simultaneous badge/checkmark/row-marker encodings for the same result. Color can reinforce the words.

The highest-value review fixtures are: **four servers succeed and one times out; cached passes become stale; credentials expire; all servers fail on first launch; and a late response for the previous release arrives after switching releases.** Verify that none can produce a misleading “Ready,” erase useful results, or move selection to a different build.