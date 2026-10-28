The working directory is empty, so I couldn't find any screens to review. If they're somewhere else, give me the path or paste them in and I'll go through them one by one. Until then, here are the states a five-server dashboard usually needs that the happy path leaves out.

## Per server (each of the five rows/panels)

The key design decision is that **each server has its own state**, and the dashboard should never fail as a whole because one server failed.

| State | What to show |
|---|---|
| **Never loaded** | A placeholder row with a spinner and the server name, so the layout doesn't jump when data arrives. |
| **Loading (first fetch)** | Spinner plus time elapsed. After about 5 seconds, show something like "still waiting on jenkins-eu…". |
| **Refreshing (has old data)** | Keep showing the old data with a small refresh indicator. Don't blank the row. |
| **Stale** | The last refresh failed but old data exists. Show the data dimmed with "as of 14:02 (3m ago)". This is the most commonly missed state, and it's dangerous: old green looks exactly like current green. |
| **Timeout** | Different from an error. "No response after 10s", with when it will retry next. |
| **Unreachable / DNS / TLS** | A short cause in plain words, e.g. "can't connect: certificate expired". |
| **Auth failed (401/403)** | Needs a different fix than a network error: "token expired, run `x login`". Don't retry it in a loop. |
| **Rate limited (429)** | "Rate limited, retrying in 45s". Back off. |
| **Bad/unexpected response** | Bad JSON, a schema change, or an HTML error page. "Unexpected response from server", with details in a log or detail view. |
| **Empty** | The server works but has no builds for this release or branch. That's a real result, not an error, so say "no builds found" clearly. |
| **Disabled / not configured** | The user turned it off, or the config is missing. Show it dimmed, or hide it with a note in the footer. |

## Build-level states (inside a server)

The happy path probably covers pass and fail. Also design for:
- queued/pending, running (with progress or elapsed time), cancelled/aborted, skipped
- flaky or retried builds (failed, then passed on retry)
- unknown or new status strings from the CI server. Have a fallback so they don't crash the UI or show up blank.
- very long names, branches, or error messages (truncate them, with a way to see the full text)
- many builds (scrolling or pagination) vs. exactly one

## Whole-dashboard states

- **Mixed:** for example, 3 servers OK, 1 stale, 1 auth error. This will be the normal case, so check that your layout holds up here rather than when everything is green.
- **All failed:** possibly your own network is down. Say "no servers reachable, check your connection" instead of showing five separate errors.
- **Summary/headline:** if there's an overall "release ready?" indicator, decide what it says when some data is missing. It should be "unknown", never "green".
- **No config / first run:** explain what to configure.
- **Offline at startup** vs. losing the network while running.

## Terminal-specific states

- **Narrow or short terminal:** decide what collapses. Five columns probably won't fit in 80 columns.
- **Resize** while running.
- **No color** (`NO_COLOR`, piped output, color-blind users): status can't rely on red/green alone, so add symbols like `✓ ✗ ● ?` and text.
- **Unicode not supported:** ASCII fallback for spinners and icons.
- **Focus/selection** on a row that's in an error state: what can the user do there? Retry this server, open the details, copy the error.

## Interaction states

- Manual refresh while a fetch is already running (ignore it, or restart?)
- Retry a single server vs. refresh all
- An error details view (full message, URL, HTTP status, timestamp)
- Quitting during a fetch

If you share the screens, I'll map each one against this list and point out which states are missing for your specific layout.
