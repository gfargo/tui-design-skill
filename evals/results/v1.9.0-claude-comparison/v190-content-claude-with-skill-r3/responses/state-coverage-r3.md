I couldn't find any screens to look at. The working directory is empty and nothing was attached. So this is the state set your dashboard needs, based on what you described. If you paste your happy-path layout, I can check it against this list and do a clutter audit on it.

## The main point: each server has its own state

With five servers, the whole screen rarely has one state. Each server does, and the screen is a mix of them. On a normal day, one server being slow or down is likely, so the partial view (some servers loaded, some not) is what users will see most often. Design that first.

The biggest risk on a release dashboard is a header that says "all green" when two servers never answered. A server that didn't respond is unknown, not passing.

## States for each server

| State | Cause | What its row shows | Action |
|---|---|---|---|
| Connecting | First fetch, no data yet | Spinner after about 200ms, with elapsed time after 2s | `Esc` cancels |
| Refreshing | Fetching again | Previous rows stay visible, with a small spinner by the server name | none |
| OK | Data arrived | The builds | none |
| OK but empty | Server answered but has no builds for this release | `no builds for v2.4.0 on buildkite` | `s` switches release |
| Unreachable | Timeout, DNS failure, connection refused | `! circle-eu unreachable (timeout 10s) ⋅ retry in 30s` | `r` retries now; retries also happen automatically, with growing delays |
| Auth failed | 401 or 403 | `✗ drone-int auth failed (401): token expired?` | Opens settings. Don't keep retrying, because retrying won't fix a bad token. |
| Rate-limited | 429 | `! gha rate-limited ⋅ resumes 14:32` | Wait for the time the server gives back |
| Bad response | Server sent unexpected data, or its API version changed | `✗ jenkins: unexpected response` | `l` shows the raw error |
| Stale | Fetches keep failing but older data exists | The last good rows, dimmed, with the label `STALE 4m` | `r` |
| Not configured | No URL or token set | `buildkite not configured` | Opens settings |

Each failure type needs its own fix (retry, wait, fix the token, file a bug), so lumping them all under "error" makes the user guess which one to try. Dimming alone disappears under `NO_COLOR`, so stale rows also need the `STALE` label.

## States for the whole screen

- **Initial (no config):** Draw the layout right away. Show the config file path and an example entry instead of a blank screen.
- **All loading:** Show the table with all five servers listed as connecting. Fill each one in as soon as it answers. One slow server must never hold up the other four.
- **Partial:** Show "3 of 5 servers OK" in the header, and put each failure inline where that server's builds would normally appear.
- **All failing:** If all five are unreachable, the problem is probably the user's own network or VPN, not five broken servers. Say that, and keep the last good data visible and marked stale.
- **All empty:** Every server answered but has no builds for this release. Name the release and offer a key to switch.
- **Too small:** `terminal too small: need 60x12 ⋅ q quit`. Keep `q` and `Ctrl+C` working.

## The header verdict

The header should state the release decision honestly:

```
READY      5/5 servers ok ⋅ all passed
BLOCKED    1 failed: web #977 (jenkins)
UNKNOWN    2 servers not reporting ⋅ 3 passed     <- never shown as READY
RUNNING    2 in progress ⋅ 3 passed
```

## Sketches

At 96 columns:

```
v2.4.0  UNKNOWN  2 servers not reporting           3 of 5 ok ⋅ refreshed 12s ago
 Source        Pipeline            Status    Age    Duration
 jenkins-main  api #1842           passed    4m     6m12s
 jenkins-main  web #977            failed    9m     3m40s
 gha           release.yml #311    running   1m     –
 buildkite     e2e #5520           passed    22m    18m03s
 circle-eu     ! unreachable (timeout 10s) ⋅ retry in 30s            r retry
 drone-int     ✗ auth failed (401) ⋅ token expired?                  c config

 r refresh ⋅ f failing only ⋅ enter details ⋅ p pause ⋅ L log ⋅ ? help
```

At 60 columns, for a tmux split: the Duration column goes first, server names shorten, and Enter opens the full details:

```
v2.4.0 UNKNOWN              3/5 ok ⋅ 12s ago
 Pipeline            Src      Status   Age
 api #1842           jenkins  passed   4m
 web #977            jenkins  failed   9m
 release.yml #311    gha      running  1m
 e2e #5520           bk       passed   22m
 ! circle-eu unreachable ⋅ retry 30s   r
 ✗ drone-int auth failed (401)         c
 r refresh ⋅ f failing ⋅ enter open ⋅ ? help
```

This is a single table, so it narrows without needing to fold into separate panes. That's better than a grid with one box per server, which has nowhere to go at 60 columns.

## Refresh behavior that's easy to miss

- **Selection:** Track the selected build by a stable ID such as server plus build number, not by row position. Otherwise a refresh moves the cursor onto a different build. If the selected build disappears, select its neighbor, not the first row.
- **Sorting:** Don't re-sort on every refresh. Rows shifting while someone reads them is the most common complaint about live dashboards.
- **Pause key:** Add a pause key (`p`). While paused, mark the header `PAUSED` and show "4 updates pending".
- **Message log:** Send every error to a log the user can reopen (`L`). Errors should stay on screen until dismissed, not fade away unread.
- **Not blocking the screen:** Fetch all five servers at the same time, each with its own timeout. Never fetch on the thread that draws the screen.
- **Status signals:** Use at most two per status: a word plus one color, for example red `failed`. Don't add `[FAIL]` and a ✗ on top of that. Passing rows can be plain text so failures stand out.

**Optional:** A `--once` mode with exit codes (0 ready, 1 blocked, 2 unknown) would let release scripts and CI wait on the same verdict without opening the full-screen dashboard.

Send the screens or the framework you're using, and I'll map these states to its loading and async patterns and check the 80×24 and 60-column layouts against what you actually have.
