**Design partial failure first: one unavailable CI server must never make the other four disappear—or make the release look fully verified.** Track build results separately from the health and freshness of each server connection.

I used the requested `tui-design` skill. No screens or project files were available in the workspace, so this is a state-coverage review rather than a visual critique.

Your dominant loop is: scan release readiness → identify a failing or unknown check → inspect its server/build → retry or wait.

| State | What the screen should say/show | Recovery or next action |
|---|---|---|
| **Initial / unconfigured** | “No CI servers configured,” or identify missing configuration. | Show where to configure servers. |
| **First load** | Render all five server slots immediately; show each as loading independently. Include elapsed time for slow requests. | Cancel fetch; inspect results as they arrive. |
| **Partial load** | “3/5 servers responded; 2 pending.” Show completed results immediately. | Keep navigation usable; retry only affected servers. |
| **Fresh / complete** | All five sources checked, with build results and observation ages. | Open build details; refresh. |
| **Background refresh** | Keep existing rows visible; label refreshing separately from build status. | Preserve selection and scroll position. |
| **Empty source** | “No builds for release v2.4 on ci-east.” | Change release/branch or inspect the source. |
| **Empty filter** | “No builds match ‘linux’.” Distinguish this from a server returning zero builds. | Clear filter. |
| **One or more fetch failures** | Keep every server represented. Name affected servers and reasons: timeout, DNS, TLS, server error. | Retry affected server; open diagnostics. |
| **Authentication / permission failure** | “ci-west: credentials expired” or “access denied.” | Explain how to update credentials or permissions; avoid endless automatic retries. |
| **Rate limited** | Identify the server and next permitted retry time. | Wait; respect the server’s retry interval. |
| **Disconnected / stale** | Retain last successful data with `STALE 4m`, plus reconnect status. With no cached data, show `UNKNOWN`. | Retry now; inspect connection details. |
| **All servers unavailable** | Persistent global warning plus five individual source states. Cached results remain visibly stale. | Retry all; inspect configuration/network. |
| **Invalid / incomplete response** | “ci-3 returned an unrecognized build status.” Preserve valid records. | Inspect diagnostics; never silently interpret unknown as passed. |
| **Recovered** | Replace stale data only after a successful response; briefly report recovery. | Keep warning history accessible. |
| **Too small** | State the required terminal dimensions. | Resize; keep quit working. |

The build itself also needs **queued, running, passed, failed, canceled, skipped, blocked/manual approval, and unknown**, where supported. An unavailable server is a **fetch failure**, not a failed build. A skipped check satisfies release requirements only if your release policy says so.

For the release summary:

- **Ready:** every required check passed for the selected release/commit, with sufficiently fresh observations.
- **In progress:** required checks are queued or running.
- **Blocked:** a required check failed or needs intervention.
- **Unverified:** required evidence is missing, stale, inaccessible, or for a different commit.

Show known failures alongside missing evidence: `Blocked: 1 failed; 2 servers unverified`.

Suggested wide layout and 60-column fallback:

```text
Wide
Release v2.4 / a1b2c3   UNVERIFIED   Fresh sources 3/5
SERVER    BUILD       FETCH          AGE | SELECTED SOURCE
> ci-1    passed      fresh           8s | ci-1 / build #812
  ci-2    running     fresh           5s | Commit: a1b2c3
  ci-3    passed      fresh           9s | Enter: build details
  ci-4    passed*     reconnecting    4m |
  ci-5    unknown     access denied    - |
* Last known result
r retry selected   R refresh all   Enter details   ? help
```

```text
60 columns
v2.4 / a1b2c3   UNVERIFIED   Fresh 3/5
SERVER   BUILD      FETCH / AGE
> ci-1   passed     fresh 8s
  ci-2   running    fresh 5s
  ci-3   passed     fresh 9s
  ci-4   passed*    STALE 4m; reconnecting
  ci-5   unknown    access denied
* Last known result
r retry   Enter details   ? help   q quit
```

At **80×24**, keep the table and move details to drill-down. At **60 columns**, retain server, result, and freshness; put URLs, durations, and diagnostic text in details. A proposed minimum is **60×12**; below it, show the truthful too-small screen.

For clutter, the proposed layout has **zero nested borders**, one textual status per meaning, and one selection marker. Avoid five separately boxed server cards, repeated release labels, and combinations such as green + checkmark + `[PASS]`. Actual chrome usage cannot be measured without your screens.

The highest-value review fixture is **three fresh servers, one stale cached pass, and one permission failure**, followed by recovery while the user has a build selected. Verify that the summary stays honest and selection stays attached to the same build as updates arrive.