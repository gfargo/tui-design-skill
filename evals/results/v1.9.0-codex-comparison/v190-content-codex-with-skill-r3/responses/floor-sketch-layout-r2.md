Use a **three-column browser that collapses to drill-down views**: namespaces → pods → details/logs. This fits the main loop: choose a namespace, scan pod health, select a pod, inspect its logs.

Keep it full-screen in the alternate screen buffer, with the cluster context always visible.

**Wide layout — 120+ columns**

```text
Context: prod-eu                         Namespace: payments
--------------------+----------------------------------------+----------------------------------------------
1 Namespaces        | 2 Pods (12)                             | 3 api-7d9f
                    | NAME             READY STATUS      RST | [Logs]  Overview  Events
  default           | api-7d9f           1/1 Running       0 | Container: api       FOLLOWING
  kube-system       | worker-8bc         0/1 CrashLoop...  6 |----------------------------------------------
  payments          | webhook-2fd        1/1 Running       0 | 14:32:01 INFO  Listening on :8080
  staging           |                                        | 14:32:04 INFO  GET /health 200
                    |                                        | 14:32:07 ERROR Upstream timeout
                    |                                        |
                    |                                        |
--------------------+----------------------------------------+----------------------------------------------
Tab focus   / filter   Enter logs   s sort   ? help   q quit
```

Allocate about **20 columns to namespaces, 40 to pods, and the remaining width to logs**. The sketch is abbreviated vertically; panes fill the available height.

- Start with focus in **Pods**. Use reverse video for its selected row and a bold focused pane title. Keep inactive selections visible with muted emphasis.
- Namespace navigation previews a choice; **Enter applies it**, avoiding repeated API requests while moving through the sidebar.
- Pod selection updates the detail preview. **Enter focuses Logs**. Show the pod name and container above every log stream so its source stays clear.
- Keep `NAME`, `READY`, `STATUS`, and restart count in the primary table. Add age when space permits; put node, IP, labels, and full status reasons in Overview.
- Default to stable name sorting. Preserve selection by **pod UID** across updates.

**Responsive behavior**

| Terminal | Layout |
|---|---|
| 120+ columns | All three panes. Give extra width to logs. |
| 100–119 columns | Hide namespace sidebar; namespace picker opens with `1`. Keep pods and logs side by side. |
| 80×24 | Full-width pod list. Enter opens full-width details; Esc returns. |
| 60–79 columns | One pane at a time. Keep name, readiness, status; hide restarts and age. |
| Below 60×12 | Show `Terminal too small: need 60x12`, current dimensions, and `q quit`. |

**60-column fallback — pod list and opened logs**

```text
Context: prod-eu / payments
[2 Pods]  12 pods
NAME                  READY STATUS
api-7d9f                1/1 Running
worker-8bc              0/1 CrashLoopBackOff
webhook-2fd             1/1 Running

1 namespaces  / filter  Enter logs  ? help  q quit
```

```text
payments / api-7d9f
[Logs]  Overview  Events
Container: api                            PAUSED +37 new
14:32:01 INFO  Listening on :8080
14:32:04 INFO  GET /health 200
14:32:07 ERROR Upstream timeout

Esc back  / search  G follow  c container  ? help
```

Resizing preserves focus, selection, filters, and log position. If logs had focus, narrowing keeps logs open.

Use a small, consistent keymap:

| Action | Keys |
|---|---|
| Move / scroll | Arrows or `j` / `k`; PgUp / PgDn |
| Change pane | Tab / Shift+Tab; `1` namespaces, `2` pods, `3` details |
| Open / return | Enter / Esc |
| Filter namespaces or pods; search logs | `/` |
| Change detail tab | `[` / `]` |
| Choose container | `c` in Logs |
| Resume / toggle log follow | `G` / `F` |
| Refresh / help | `r` / `?` |

Printable shortcuts yield while typing. Esc cancels input or dismisses overlays before returning from details; `q` goes back from nested views and quits at the root. Ctrl+C cancels a foreground operation or exits cleanly.

Logs open in **FOLLOWING** mode. Scrolling upward pauses following without stopping ingestion; show `PAUSED +37 new`. Keep columnar logs unwrapped with horizontal scrolling and a `w` wrap toggle. Cap retained lines and report when older lines have been dropped.

Design the unhappy paths inside the affected pane:

- **Initial/loading:** render the layout immediately; show `Loading pods...`. Retain existing rows during refresh.
- **Empty:** distinguish `No pods in payments` from `No matches for "worker"`; offer namespace selection or filter clearing.
- **Partial/error:** keep the pod list usable if logs fail. Say `Logs forbidden for container api` or `Container has not started`, with an applicable next action.
- **Disconnected:** retain the last data with `STALE 42s — reconnecting`; mark interrupted log streams explicitly.
- **Selected pod deleted:** select the nearest surviving row and show a brief notice. Never leave old logs labeled as the new pod.

Keep the visual treatment restrained. Use terminal foreground/background defaults, semantic warning/error colors paired with status text, and support `NO_COLOR` plus ASCII separators. Provide a linear `--no-tui` mode for accessible reading and scripts.

The clutter budget: **border nesting depth 0**, two vertical dividers, no boxes around individual widgets, no marker repeated on every row. Selection uses reverse video alone; health uses status text plus optional color. At 120×24, three full-width header/footer rows plus two dividers occupy roughly **14% of cells**, before table labels. Remove repeated namespace/container prefixes from every row or log line—the pane headers already carry that context.