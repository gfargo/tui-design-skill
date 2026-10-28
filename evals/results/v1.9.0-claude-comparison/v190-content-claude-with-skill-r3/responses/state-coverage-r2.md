I couldn't find any screen files in the working directory, so I haven't seen your screens. This is the state set a five-server build dashboard needs. If you share your mockups or code, I'll check them against it.

## The main recommendation

**Track state for each server, not for the whole screen. And never show "unknown" as passing.**

With five servers, one of them being down or slow is the normal case. So your most common real screen is the partial state. The worst thing this tool can do is show a green, ready-looking dashboard when it's missing a server it couldn't reach. Someone ships a release because the failing build is on the server that timed out. Every other state below matters less than this one.

So if the dashboard gives any overall release verdict, it needs three values, not two:

```
READY      all 5 servers answered, all required builds PASS
BLOCKED    at least one required build FAIL
UNKNOWN    2 of 5 servers unreachable. Can't confirm the release.
```

## Sketches

**Wide (100+ columns): the partial state, which you'll see most often**

```
 release v2.14.0-rc3   UNKNOWN  1 server unreachable           updated 12s ago
 jenkins ✓  buildkite ✓  gha ✓  gitlab ✓  circleci ✗ 6m

 Server     Pipeline            Status     Age    Duration
 jenkins    api / main          PASS       3m     4m12s
 jenkins    web / main          FAIL       8m     2m03s
 buildkite  mobile / release    ⠹ running  1m     1m40s
 gha        infra / main        PASS       22m    6m55s
 circleci   docs / main         STALE      6m     last: PASS

 ! circleci: timeout after 10s · retry in 20s · r retry now · l log
 r refresh ⋅ / filter ⋅ enter details ⋅ p pause ⋅ ? help
```

Server health lives in exactly one place, the strip under the title. It isn't repeated on every row. The circleci row stays visible, dimmed and marked `STALE` with its age, instead of disappearing.

**Floor (60 columns, e.g. a tmux split)**

```
 v2.14.0-rc3  UNKNOWN          servers 4/5  ✗circleci
 jenkins
   api / main          PASS       3m
   web / main          FAIL       8m
 buildkite
   mobile / release    ⠹ running  1m
 circleci  STALE 6m
   docs / main         last PASS  6m
 r refresh ⋅ enter details ⋅ ? help
```

What changes as the terminal narrows:
- **At 80×24:** the Duration column goes.
- **At 60 columns:**
  - The Server column becomes group headings.
  - The health strip shrinks to `4/5 ✗circleci`.
  - Error details move to the message log (`l`) and the detail view (`Enter`).
- **Below about 50×10:** show "terminal too small: need 50x10". `q` and `Ctrl+C` still work.

## The states it needs

### Screen-level states

| State | What it shows | Next action |
|---|---|---|
| **Not configured** | "No CI servers configured" plus the config path | `e` edit config |
| **First load** | Draw the layout immediately. Each server gets its own spinner, and rows appear as each server answers, so the fast four don't wait for the slow one. Show elapsed time per server after about 2s. | `Esc` cancel |
| **Partial** (normal case) | The sketch above: an `n of 5` count, failed servers marked inline, verdict `UNKNOWN` | `r` retry |
| **All unreachable** | All five failing at once is probably *your* network or VPN, not five outages. Say that, keep the last-known data dimmed, and don't show five separate error toasts. | `r` retry, `l` log |
| **Empty** | Name the scope. "No builds for v2.14.0-rc3 on any server" is different from "Filter `web` matches 0 of 14 builds". | change release / `Esc` clear filter |
| **Refreshing** | Keep the old rows visible and only update the "updated Ns ago" text. Track the selected row by `server+pipeline+build-id`, not by row number, so the cursor doesn't jump. | (none) |
| **Stale** | The last good data, dimmed, labeled `STALE` with its age, plus "reconnecting (3)" | `r` retry now |
| **Paused** | A `PAUSED` label and a count of pending updates, so you can read a failure without rows reordering | `p` resume |
| **Too small** | The needed size | `q` quit |

### Server failures need different recovery actions

Don't collapse these into one "error" state. Each needs a different action:

- **Timeout or unreachable:** retry with backoff and show when the next retry happens.
- **401/403, expired token:** stop retrying, since a retry loop won't fix credentials. Say "circleci: token rejected" and point to where the token is configured.
- **429, rate limited:** show the reset time and wait until then. Don't keep hammering it.
- **5xx or malformed response:** "circleci returned an unexpected response", with the details in the log.
- **Slow but alive:** an elapsed counter on that server only, not a global spinner.

### Build statuses beyond PASS/FAIL

- `running` and `queued`
- `cancelled`
- `skipped`
- **Status strings the server sends that you don't recognize:** show these as `?` with the raw value in the detail view. Never quietly treat them as PASS.

## Rules that apply to every state

- **One color cue plus one non-color cue at most.** For example `FAIL` in red, or `✗` in red. That way states stay readable under `NO_COLOR`. Passing rows get no marker at all, and markers are kept for exceptions.
- **Errors stay until dismissed**, then go to a message log (`l`) with timestamps. A failure that fades away unread can't be acted on.
- **A temporary failure must never change config.** Don't remove or hide a server from the saved list because it was down.
- **Never fetch on the UI thread.** Each server fetch runs on its own and reports back as a message: `ServerOk{id, builds}` or `ServerFailed{id, kind, err}`.

## How to test it

Put this logic in a pure function that takes the current state and a server result and returns the new state. Unit-test it with fake responses for each failure type above. Then save golden snapshots of the rendered screen for:
- 2 of 5 servers failed
- all servers failed
- auth error
- empty filter

Render each one at 100 columns, 80×24, and 60 columns.

If you share the happy-path screens and tell me the framework, I'll go through them for clutter (nested borders, repeated status signals) and work out the column-dropping order for your actual layout.
