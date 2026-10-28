I couldn't find your screens. The working directory (`…/tui-design-claude-run-b80nesk9`) is empty, and nothing dashboard-related turned up in the parent temp folder. If you paste the mockups or point me to the files, I'll review them against what you actually designed.

In the meantime, here are the states a dashboard that pulls from five CI servers needs. With five sources, the main risk isn't that everything fails at once. It's that some sources fail while others work, and the screen still looks fine.

## 1. Startup and loading
- **First load:** no data yet. Show each of the five servers as its own row with a "connecting…" spinner, not a blank screen or one global spinner.
- **Partial load:** three servers have answered and two are still loading. Show the results as they arrive; don't wait for the slowest server.
- **Slow load:** after about 5–10s, change "loading" to "still waiting on ci-3 (12s)…" so the user knows what's slow.

## 2. Per-server failures (the most important group)
Each server needs its own error state in its own row, so one failure doesn't take down the whole view:
- **Unreachable:** DNS failure, connection refused, network down.
- **Timeout:** different from unreachable, because the server may just be overloaded.
- **Auth failure (401/403):** expired token. Tell the user how to fix it ("token expired, run `x login`"); retrying won't help.
- **Rate limited (429):** show when the next retry will happen.
- **Server error (5xx)** or **bad response:** the API changed or returned HTML instead of JSON.
- **Misconfigured:** bad URL or missing credentials in the config. This is caught at startup, not at fetch time.

Each of these needs a clear message, a way to retry that one server, and a way to see the raw error details.

## 3. Stale data
This is the state happy-path designs miss most often.
- **Last fetch failed, but older data exists:** keep showing the old data, mark it clearly ("as of 14:02, 6 min ago ⚠"), and dim it. Never show old data looking like fresh data. A green build from 20 minutes ago may be red now.
- Show a **"last updated" timestamp** per server, not just one global timestamp.
- **Refreshing over existing data:** use a small indicator; don't clear the screen and show a spinner again.

## 4. Summary and rollup
- **What "release is green" means when one server is unknown:** it must not show green. You need a third state, "unknown/incomplete", alongside pass and fail.
- **Mixed results:** for example "4 passing · 1 failing · 0 unknown". Failures and unknowns should sort to the top or be easy to jump to.
- **All five servers down:** a full-screen state that suggests checking your network or VPN, since all five failing at once is probably a local problem, not five CI problems.

## 5. Empty and edge data
- **No builds yet** for a branch or pipeline (empty, not an error).
- **Build in progress or queued:** show elapsed time; a build stuck in queue for 40 minutes may itself be a problem.
- **Cancelled, skipped, or flaky (passed on retry):** decide whether these count as green.
- **Very long names, many pipelines, or a narrow terminal:** decide what gets cut or collapsed first.
- **Unicode or no color:** status must still be readable without color (✓ ✗ ? glyphs or text), for `NO_COLOR` or limited terminals.

## 6. Interaction states
- **Manual refresh while a fetch is already running:** ignore it or queue it, but don't send duplicate requests.
- **Drill-down detail view** for a single failing build, and what happens if fetching that detail fails.
- **Help or keybinding overlay,** plus a way to quit while loading (Ctrl-C must work even when a fetch hangs).
- **Terminal resize** in the middle of rendering.

## Suggested minimum set
If you only add a few, add these:
1. One status per server: loading, ok, error (with a reason), or stale.
2. An "unknown" result in the overall rollup, so a server that didn't answer never reads as green.
3. "Last updated" timestamps, with stale data dimmed.
4. Retry for a single server, with error details.
5. A full-screen state for when everything is down.

Send the screens and I'll map these onto your layouts specifically.
