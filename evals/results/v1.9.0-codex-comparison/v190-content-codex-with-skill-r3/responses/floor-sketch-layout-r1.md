Use a **full-screen, three-pane browser**: namespaces → pods → detail. Start focus in the pod list; selecting a pod updates its detail pane. Give logs the most width.

The main loop is: choose namespace, filter pods, inspect status, read logs, switch container, return to the list.

**Wide layout — 140×36**

```text
Context: prod-us-east                         Namespace: payments     Watch: LIVE
──────────────────┬──────────────────────────────────────────┬────────────────────────────────────────────────
1 Namespaces      │ > 2 Pods                         3/18     │ 3 Detail: api-7c9d-2km
                  │ NAME               READY STATUS      RST │ [Logs]  Overview  Events
  All namespaces  │ api-7c9d-2km       1/1   Running       0 │ Container: api (1/2)   Source: Current
  default         │ api-7c9d-6ws       1/1   Running       0 │ FOLLOWING
  kube-system     │ worker-56b-f8p     0/1   CrashLoop... 12 │
  payments        │                                          │ 14:32:08 INFO  request completed
  staging         │                                          │   method=GET path=/health status=200
                  │                                          │ 14:32:09 ERROR upstream timeout
                  │                                          │   host=ledger:8080 elapsed=5000ms
                  │                                          │
                  │                                          │
──────────────────┴──────────────────────────────────────────┴────────────────────────────────────────────────
Tab pane  ↑↓ select  / filter  Enter logs  s sort  ? help  q quit
```

Allocate about **18 columns to namespaces, 44 to pods, and the remainder to detail**. Use shared separators, without an outer box. In the actual UI, reverse video marks the focused row; the `>` in the pane title marks focus. Inactive selections remain visible with muted emphasis.

Keep the cluster context visible at every size. Show the full namespace, pod name, and container in detail, even when list values are truncated.

**Responsive layout**

| Terminal size | Layout |
|---|---|
| ≥120 columns, ≥24 rows | Three columns, as above. |
| 80–119 columns, ≥24 rows | Namespace picker; pod list above detail. At 80×24, allocate roughly 8 rows to pods and 11 to detail after headers and footer. |
| 60–79 columns, or 12–23 rows tall | One pane at a time. Preserve selection and scroll position when switching. |
| Below 60 columns or 12 rows | Show `Terminal too small: need 60×12; current W×H` and a quit hint. Resume on resize. |

At **60×24**, pods win initially; `Enter` opens full-width detail, and `Esc` returns:

```text
Context: prod-us-east   Namespace: payments
1 Namespaces  [2 Pods]  3 Detail
────────────────────────────────────────────────────────────
Pods 18                                   / filter  s sort
NAME                         READY STATUS              RST
api-7c9d-2km                 1/1   Running               0
api-7c9d-6ws                 1/1   Running               0
worker-56b-f8p               0/1   CrashLoopBackOff     12













────────────────────────────────────────────────────────────
↑↓ select  Enter detail  1 namespaces  ? help  q quit
```

**Interaction contract**

- `Tab` / `Shift+Tab` cycle panes; `1`, `2`, `3` jump directly. At narrow sizes these also switch the visible pane.
- `↑`/`↓` and `j`/`k` navigate. Namespace selection commits with `Enter`, then focuses pods.
- `/` filters namespaces or pods; in logs it searches, with `n`/`N` for matches. Show filtered counts and the active query.
- `Enter` on a pod focuses its logs. `[` / `]` switch **Logs / Overview / Events** within detail.
- In logs: `c` chooses a container, `p` toggles current/previous container logs, `w` toggles wrapping.
- Upward scrolling pauses follow and shows `PAUSED · 37 new`. `G` resumes following. New arrivals never move a paused viewport.
- `Esc` dismisses input or overlays, clears an active filter, then returns from detail. `q` quits outside text entry; `Ctrl+C` cancels an active interaction or quits. Keep `? help` visible.

Use a contextual footer: log focus replaces list commands with `↑↓ scroll  / search  G follow  c container  w wrap`.

**Live data and failure states**

Track pod selection by **UID**, preserving its screen position during updates. Default to stable name sorting. If the selected pod disappears, select its nearest surviving neighbor and explicitly report the deletion.

Keep failures local to their pane:

| State | Presentation |
|---|---|
| Initial/loading | `Loading pods…`; keep the layout stable. |
| Empty | Distinguish `No pods in payments` from `No pods match "worker"`. |
| Partial access | Show accessible data and label the denied scope. |
| Logs unavailable | Explain `Container waiting`, `No previous logs`, or `Logs forbidden`; retain pod metadata. |
| Disconnected | Preserve data with `STALE · last update 14:32:08 · reconnecting`. |
| Success | Pod watch says `LIVE`; log stream separately says `FOLLOWING`, `PAUSED`, or `ENDED`. |

Cap retained logs and disclose dropped lines. Ignore late log responses after the selected pod or container changes.

**Visual budget**

Border nesting is **zero**; only shared pane dividers remain. Use one selection cue, one focus cue, and status text with optional semantic color. Remove per-row bullets, healthy checkmarks, repeated namespace values within a single namespace, and boxed metadata fields. Add a namespace column only in “All namespaces.”

Reserve roughly five rows for global and pane chrome; spend the remaining height on data. Keep table rows single-line, measure terminal cell widths, and support monochrome, ASCII separators, and a linear `--no-tui` mode for pod listings and logs.