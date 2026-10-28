Use a **persistent three-pane layout on wide terminals**, with the pod list as the main workspace and logs following the selected pod. On smaller terminals, switch to a single-pane drill-down.

The core loop is: choose namespace → filter pods → select pod → inspect logs → switch container or read earlier output.

Wide layout, at 140×32; rows abbreviated:

```text
Context: production-us-east   Namespace: payments                         LIVE

1 Namespaces      | 2 Pods: 18                           | 3 Detail
                  | NAME             READY STATUS   RST | api-7d9f-k2p
  default         | api-7d9f-k2p        1/1 Running    0 | [Logs] Summary Events
  kube-system     | api-7d9f-m8q        1/1 Running    0 | Container: api   FOLLOW
  payments        | worker-65bc-x4n     0/1 Pending    0 |
  monitoring      | worker-65bc-z9r     0/1 CrashLoop  6 | 14:32:01 INFO listening :8080
                  |                                     | 14:32:04 INFO GET /health 200
                  |                                     | 14:32:08 ERROR upstream timeout
                  |                                     | 14:32:09 INFO retry succeeded
                  |                                     |
                  |                                     |

Tab focus   / filter   Enter logs   s sort   ? help   q quit
```

Allocate roughly **22 columns to namespaces, 50 to pods, and the remainder to detail**, with only shared separators. Start focus in Pods. In the actual UI, use reverse video for the selected row and a bold, accent-colored title for the focused pane.

At **60 columns**, show one pane at a time:

```text
production-us-east / payments
1 Namespaces  [2 Pods]  3 Detail
Pods 18
NAME                         READY STATUS
api-7d9f-k2p                   1/1 Running
api-7d9f-m8q                   1/1 Running
worker-65bc-x4n                0/1 Pending
worker-65bc-z9r                0/1 CrashLoop

/ filter  Enter logs  1 namespaces  ? help  q quit
```

Selection is reverse video here too; the full pod name and full Kubernetes status/reason remain available in Detail.

| Terminal size | Layout behavior |
|---|---|
| 120+ columns | All three panes; give extra width to logs. |
| 80–119 columns | Full-width pod list; `1` opens namespaces, `Enter` opens detail. At 80×24, retain age and restart columns when they fit. |
| 60–79 columns | Single pane; retain name, readiness, and status. Hide age and restarts first. |
| Below 60×12 | Show `Terminal too small — need 60 columns × 12 rows`, current dimensions, and quit control. |

Resizing preserves focus, selection, filters, and log position. If Detail is focused when the terminal narrows, keep Detail visible.

**Keyboard behavior**

| Key | Action |
|---|---|
| `Tab` / `Shift+Tab` | Cycle panes in reading order |
| `1` / `2` / `3` | Open or focus Namespaces / Pods / Detail |
| `↑` / `↓`, `j` / `k` | Move selection or scroll |
| `Enter` | Commit namespace selection; from Pods, focus Logs |
| `/` | Filter the focused list; search within logs |
| `[` / `]` | Switch Detail tabs |
| `c` | Choose container in Logs |
| `F` / `G` | Toggle follow / jump to newest log |
| `w` | Toggle log wrapping |
| `Esc` | Dismiss input or overlay, clear a filter, then return one drill-down level |
| `?` | Contextual help |
| `q` | Back from nested detail; quit at the root |
| `Ctrl+C` | Cancel active input or operation; otherwise quit |

Printable shortcuts apply only outside text entry. The footer changes with focus—for logs, show search, container, follow, wrap, and back controls.

**Details that make this work**

- Namespace arrows move the highlight; `Enter` changes scope. Keep the active namespace in the header so browsing the sidebar does not silently change the pod list.
- Detail shows the selected pod’s full name, container, and tabs: **Logs**, Summary, Events. Default to Logs; briefly debounce selection changes before replacing the stream.
- Preserve pod selection by **UID**, not row number. Refreshes must not move the viewport under the cursor. If the pod disappears, choose the nearest surviving row and announce the change.
- Logs open in `FOLLOW`. Scrolling upward pauses following and shows `PAUSED · 37 new`; incoming lines never pull the reader downward. Keep a bounded buffer and disclose dropped history.
- Use textual statuses with optional semantic color: yellow for pending, red for failures. Honor `NO_COLOR`; no icon font is required.

Handle states locally: loading belongs in the pane fetching data; an empty namespace says “No pods”; an empty filter says “No matches — Esc clears filter.” Log permission errors leave pod browsing usable. Disconnects retain cached data under `STALE · last update 14:32:09`, with retry status. Pending pods show “Container not started” and offer Events.

The clutter audit is deliberately small: **border depth 0**, two shared separators, no markers repeated on every row, and at most a status word plus color for health. Remove an outer frame, nested log boxes, repeated namespace/container prefixes, and full dates on every same-day log line. At 140×32, reserve about 15–20% of cells for titles, labels, separators, and controls.

Run this as an alternate-screen session with clean terminal restoration. Provide a linear `--no-tui` mode for accessible reading and automation; keep debug output away from the active screen.