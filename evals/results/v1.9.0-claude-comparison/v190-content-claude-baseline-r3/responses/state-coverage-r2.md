I couldn't find your screens. The working directory (`/private/var/folders/.../tui-design-claude-run-gwvijc8m`) is empty, so I can't comment on your actual layouts. If you paste the mockups or point me at the files, I'll go through them screen by screen.

In the meantime, here are the states a dashboard pulling from five CI servers usually needs beyond the happy path. The key point is that with five independent sources, **most states apply per server, not to the whole screen.** Your happy path probably shows all five as one result, and the real design work is in mixed results.

## Per-server states (each row or panel)

| State | What to show |
|---|---|
| **Loading (first fetch)** | A placeholder or spinner in that row only. Fill in the other rows as their data arrives instead of blocking on the slowest server. |
| **Refreshing (has data)** | Keep the old data visible with a small refresh indicator. Don't blank the row. |
| **Stale** | The last good data plus its age ("updated 4m ago") in a dimmed style. This is the most common real-world state. |
| **Timeout** | Different from an error: the server may just be slow. Say "no response after 10s" and keep retrying. |
| **Unreachable / network error** | Show which server it is, a short reason, and when the next retry happens. |
| **Auth failure (401/403)** | Retrying won't fix this, so say so and point at the config or token. Don't show it as a generic error. |
| **Rate limited (429)** | Show the backoff time. Retry on its own schedule. |
| **Bad or unexpected response** | Say "Couldn't parse response from X", and in a debug view show the raw text, not a stack trace. |
| **No builds / empty** | A new pipeline or filtered-out branch is a valid state, not an error. Make it look different from "failed to load". |
| **Disabled / not configured** | If someone turns a server off, show it as intentionally absent so it doesn't read as broken. |

## Build-status states (inside the data)

Your happy path probably covers pass/fail. Also check for: **running** (with elapsed time), **queued**, **cancelled**, **skipped**, **flaky or retried**, and **unknown status**, meaning a value from the CI API that your code doesn't map. The last one needs a fallback rendering so new API values don't break the row.

## Whole-dashboard states

- **Cold start:** nothing loaded yet. Show the five server names right away with loading placeholders so the layout doesn't jump.
- **Partial failure:** for example 3 OK and 2 failing. This is the most important screen to design. The summary or header needs a clear rollup like "2 sources unavailable". Releasing based on incomplete data is the real risk.
- **All sources down:** probably your own network or VPN. Say that directly rather than showing five separate errors.
- **Conflicting data:** if two servers report on the same release and disagree, decide whose status wins or show both.
- **Offline or cached:** if you cache, show cached data clearly labelled with when it was fetched.
- **Config error at startup:** a missing or invalid config file should give a readable message before the TUI starts, not a crash inside it.

## Terminal-specific states

- **Narrow or short terminal:** decide what collapses (hide columns, shorten names) and set a minimum size with a "resize to at least N×M" message.
- **No color / `NO_COLOR` / colorblind users:** pass, fail and stale must be distinguishable without color, using symbols like ✓ ✗ ⟳ ? and text.
- **Long names:** truncate branch or job names with an ellipsis and decide which end to cut.
- **Resize during refresh:** make sure a redraw doesn't corrupt the layout.
- **Non-TTY / piped output:** if anyone runs it in a script, consider a plain-text or JSON mode.

## Interaction states

- **Manual refresh in progress:** stop double-triggers and show that the refresh was received.
- **Error detail view:** a way to expand one server's error to see the full message, URL and last success time.
- **Focus or selection on a row that disappears** after a refresh.
- **Help overlay** listing the keybindings.

## Where I'd start

If you only add a few, design these first:
1. **Partial failure**, including the summary rollup.
2. **Stale data with age shown.**
3. **Auth error as its own state, separate from network errors.**
4. **No-color rendering.**

Together these cover most of what will actually go wrong day to day. Send the screens and I'll map these onto your layouts.
