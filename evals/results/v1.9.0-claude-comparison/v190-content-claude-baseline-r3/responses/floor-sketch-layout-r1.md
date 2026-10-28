The project directory is empty, so this design doesn't assume a particular framework. It works with Bubble Tea, Ratatui, Textual or tview.

## Recommended layout: sidebar, pod list on top, details and logs below

Log lines are long, so the main design choice is to give logs the **full width of the right side** rather than a narrow third column.

```
┌─ kpods ── ctx: prod-us-east-1 ───────────────────────────────────────────────────── ↻ 2s ago ─ ? help ─┐
├─ Namespaces ──────┬─ Pods (default) ── 14 ── filter: api_ ──────────────────────────────────────────────┤
│ ▸ All         142 │   NAME                          READY  STATUS             RESTARTS  AGE    NODE      │
│   default      14 │ ▶ api-7f9c8d-x2kqp              2/2    ● Running                 0  3d     node-a    │
│   kube-system  23 │   api-7f9c8d-mm81z              2/2    ● Running                 1  3d     node-b    │
│   monitoring    9 │   api-7f9c8d-q0p4c              1/2    ◐ CrashLoopBackOff       17  3d     node-c    │
│   payments      6 │   api-migrate-28461-hj2       0/1    ✓ Completed               0  2h     node-a    │
│   staging      31 │   api-canary-5d6b-zz91          0/2    ○ Pending                 0  12s    —         │
│                   │                                                                                    │
│                   ├─ api-7f9c8d-x2kqp ─ [Logs] Info  Events  YAML ─────────────── container: api ▾ ────┤
│                   │ 14:02:11.381 INFO  http  GET /healthz 200 1.2ms                                    │
│                   │ 14:02:11.902 INFO  http  POST /v1/orders 201 48ms                                  │
│                   │ 14:02:12.044 WARN  db    slow query (412ms): SELECT * FROM orders WHERE …          │
│                   │ 14:02:12.517 ERROR auth  token verification failed: jwt expired                    │
│                   │ 14:02:13.001 INFO  http  GET /healthz 200 0.9ms                                    │
│                   │                                                                                    │
│ / filter          │ ● following   wrap:off   ts:on   since: 15m             /search  2 of 7 matches   │
├───────────────────┴────────────────────────────────────────────────────────────────────────────────────┤
│ tab focus  ↑↓/jk move  enter select  / filter  l logs  f follow  w wrap  s shell  d delete  q quit    │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Regions and sizing

| Region | Size | Notes |
|---|---|---|
| **Header** | 1 row | Context/cluster (show it in red if it matches `prod`), refresh age and a help hint. |
| **Namespace sidebar** | Fixed at 18–22 columns | Pod count on the right, with `All` pinned at the top. Truncate long names with `…`. |
| **Pod list** | About 40% of the right-side height, at least 5 rows | Sortable table. Adapt columns to width (see below). |
| **Detail pane** | Remaining height | Tabbed: **Logs** (default), Info, Events, YAML. |
| **Log status line** | 1 row, inside the detail pane | Follow state, wrap, timestamps, time range, search matches. |
| **Footer** | 1 row | Key hints that change with the focused pane. |

## Focus model

- Three focusable panes: `Tab` / `Shift-Tab` cycles through them, and `1` / `2` / `3` jumps directly.
- The focused pane gets a **bright or double border and a highlighted title**. Unfocused panes use dim borders.
- Selection flows left to right: picking a namespace filters pods, and moving the pod cursor updates the detail pane. Debounce this by about 150 ms so scrolling quickly doesn't open a log stream for every pod.
- `Enter` on a pod moves focus to the logs. `Esc` steps focus back out one level.
- `z` zooms the focused pane to full screen. This is the most useful extra for logs.

## Pod list

- **Status uses both a glyph and a color**, so it still reads on monochrome terminals and for colorblind users:
  - `●` green: Running
  - `◐` red: CrashLoopBackOff or Error
  - `○` yellow: Pending
  - `✓` dim: Completed
  - `✗` red: Failed
- A row with READY lower than its total (for example `1/2`) is tinted yellow, even if the status is Running.
- RESTARTS is right-aligned and bold when it's above 0.
- Column priority as width shrinks: NAME > STATUS > READY > AGE > RESTARTS > NODE > IP.
- `/` filters inline (fuzzy match on name). `S` cycles the sort column.

## Detail pane tabs

- **Logs:** follow mode is on by default. Scrolling up pauses following and shows `⏸ paused — G to resume`. Color the level tokens, keep timestamps in a dim fixed-width column, and use `/` to search with `n`/`N`. For pods with multiple containers, `c` opens a container picker. `p` shows logs from the previous container instance, which matters most for CrashLoopBackOff.
- **Info:** labels, IP, node, QoS class, and per-container image, state and resources in a compact key/value grid.
- **Events:** newest first, with Warning events highlighted. This is often the fastest way to explain a Pending pod.
- **YAML:** read-only and syntax-highlighted.

## Responsive breakpoints

| Width | Behavior |
|---|---|
| ≥ 140 | Optional: put details to the right of the pod list (three columns). Only worth it on very wide screens. |
| 100–139 | The layout above. |
| 80–99 | The sidebar collapses to a 1-row namespace selector in the header (`ns: default ▾`, opened with `n`). |
| < 80 | One pane at a time with breadcrumbs (`ns › pod › logs`). `Enter` goes deeper and `Esc` goes back. |

When the terminal has fewer than about 24 rows, the pod list shrinks to 5 rows and the detail pane keeps the rest.

## States worth designing explicitly

- **Loading:** a spinner in the pane title, not a full-screen blocker.
- **Empty namespace:** a centered dim message, `No pods in payments`.
- **RBAC forbidden:** show it in the pane (`✗ forbidden: cannot list pods in kube-system`) and keep the rest of the app usable.
- **Connection lost:** the header turns red and shows `⚠ disconnected — retrying in 5s`, with stale data dimmed.
- **Destructive actions** (`d` delete, `K` kill): a confirmation modal that requires typing the pod name in prod contexts.

If you tell me which framework you're using, I can turn this into a working layout skeleton with the panes, focus handling and resize breakpoints.
