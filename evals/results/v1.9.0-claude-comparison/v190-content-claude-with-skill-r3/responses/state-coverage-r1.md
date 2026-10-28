I couldn't find any screens: the working directory is empty and nothing was attached. So this is the state list your dashboard needs, based on the skill's States guidance. If you paste the frames or point me at the code, I'll check them against it.

## The main point: track state per server, not per screen

With five independent CI servers, the dashboard's overall state comes from five separate fetch states. Usually some servers will be loading, failed or stale while others are fine, so plan for mixed results as the normal case. Each server needs its own fetch state. The screen-level states are summaries of those.

The worst failure is a dashboard that says "ready to release" when one server never answered. **A server that didn't answer is unknown, not a pass**, and the release verdict has to say so.

## Per-server states (one row each)

| State | Cause | What the row shows | Action |
|---|---|---|---|
| **Not fetched yet** | Startup | Server name, `⠋` after about 150 ms | — |
| **Loading (first time)** | First request in flight | Spinner, then elapsed time after 1–2 s | `Esc` cancel |
| **Refreshing** | Later request in flight | Last-known values stay; small spinner in the Updated column | — |
| **OK** | Data received | passed / failed / running / queued / cancelled | `enter` details |
| **No builds** | Server works but has no builds for this release, ref or tag | `– no builds for v2.14.0` | Say which ref was queried |
| **Unreachable / timeout** | DNS, refused connection, VPN down, per-server timeout | Last known value dimmed + `STALE 6m` + `! timeout` | `r` retry, backoff count |
| **Auth failed** | Token expired or 401/403 | `✗ auth expired`, no automatic retry loop | Tell the user which env var or config key to fix |
| **Rate limited** | 429 | `… rate limited, retry in 40s` | Follow Retry-After |
| **Bad response** | Schema or API version changed, parse error | `✗ unexpected response`, details in the message log | `l` log |
| **Stale** | Last success older than a set age | Dimmed + `STALE <age>` even if no error has been shown yet | `r` retry now |

Keep **"build failed"** (a fact about CI) visually separate from **"couldn't fetch"** (a fact about your connection). If both show up as a red ✗, users will rerun builds that are fine. Builds get `✓ passed` / `✗ failed`. Fetch problems get `?` or `!` plus a reason, placed in a different column from build status.

## Screen-level states

- **Initial / not configured.** No servers configured, or the config is missing. Show the config path and an example, not an empty table.
- **All loading.** Draw the table straight away with all five server names and a spinner on each row. A blank screen looks like the app has hung.
- **Partial.** The header shows `4 of 5 sources`. Mark each failed source on its own row with a retry key, and never blank the screen because one server failed.
- **All unreachable.** This usually means *your* network or VPN is down, not CI. Say that (`all 5 servers unreachable: check network/VPN`) instead of showing five separate errors.
- **All OK.** The verdict line shows the result. A manual refresh confirms with `✓ refreshed` in the status line, which fades after 3–5 s.
- **Verdict.** Use three values, never two: `READY`, `NOT READY (1 failed)`, `UNKNOWN (1 unreachable)`. If a server is unknown, the verdict is unknown.
- **Too small.** Show `terminal too small: need 50x10`, and keep `q` and `Ctrl+C` working.
- **Paused.** If you auto-refresh, offer a freeze key and show `PAUSED` in the header, so rows don't move while someone reads them.

## Layouts

Wide (around 90+ columns):
```
 release v2.14.0                       4 of 5 sources · updated 12s ago

 Server      Pipeline        Build        Time    Source
 jenkins-1   build-linux     ✓ passed    4m12s   12s ago
 jenkins-2   build-windows   ✗ failed    6m03s   12s ago
 gha         test-matrix     ⠹ running   2m40s   now
 buildkite   integration     ✓ passed    3m55s   STALE 6m ! timeout
 circle      docs            – no builds          12s ago

 NOT READY: 1 failed, 1 unknown (buildkite)
 r refresh ⋅ R retry failed ⋅ enter details ⋅ p pause ⋅ ? help
```
The buildkite row is dimmed: it's the last known value, not a confirmed pass.

Floor (60 columns, tmux split): drop the Pipeline column, and only show source health when something is wrong:
```
 v2.14.0  NOT READY                     4/5 · 12s
 jenkins-1   ✓ passed    4m12s
 jenkins-2   ✗ failed    6m03s
 gha         ⠹ running   2m40s
 buildkite   ✓ passed    STALE 6m !
 circle      – no builds
 r refresh ⋅ enter details ⋅ ? help
```
Pipeline name, error text and logs move to the `enter` detail view. Below about 50×10, show the too-small message.

## Behavior to get right while you're in there

- **Fetch each server concurrently with its own timeout**, and never on the UI thread. One slow server must not hold up the other four.
- **Back off retries per server.** Don't retry auth failures automatically.
- **Keep the selection on the server's ID, not its row number**, so the cursor doesn't jump when a refresh reorders rows. Don't re-sort on refresh.
- **Keep errors until they're dismissed**, then send them to a message log the user can reopen (`l`). Five servers failing at once shouldn't produce five toasts. Group them into one status line and send the detail to the log.
- **Don't save transient failures to config.** An unreachable server should never be removed or disabled in config automatically.
- **Use one colour cue plus one non-colour cue per status** (`✗ failed` in red). Don't add a `[FAIL]` tag or row marker as well. Everything must still read correctly under `NO_COLOR`, and `?`/`!`/`–` need an ASCII fallback.

## Tests to pin

- Unit-test the verdict function on combinations of the five servers' states, especially "4 pass + 1 timeout ⇒ UNKNOWN".
- Golden-frame tests at 90 columns, 80×24 and 60 columns for: all loading, partial, all unreachable, stale, auth expired and too small.

Send the screens you have and I'll check each one against this list, count the clutter, and check how they hold up at 60 columns.
