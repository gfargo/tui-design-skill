The directory is empty, so this is a design spec, not code. Here's what I'd recommend.

## Layout

```
 kube-tui   ctx: prod-us-east   cluster: eks-prod                         ⟳ 2s ago   v1.31
┌─ Namespaces ─────┐┌─ Pods · default (14) ─────────────────────────────────────── filter: api ─┐
│   all         61 ││   NAME                     READY  STATUS            RESTARTS  AGE   NODE  │
│ ▸ default     14 ││ ▸ api-7f9c8d-x2k4p         2/2    Running           0         3d    n-01  │
│   kube-system 22 ││   api-7f9c8d-q8rtz         2/2    Running           1         3d    n-02  │
│   monitoring   9 ││   worker-5b6d4-mm2lc       0/1    CrashLoopBackOff  17        42m   n-03  │
│   ingress      3 ││   worker-5b6d4-p9vns       1/1    Running           0         42m   n-01  │
│   payments    13 ││   migrate-28817-zt5qd      0/1    Completed         0         6h    n-02  │
│                  ││   redis-0                  1/1    Running           0         12d   n-04  │
│                  │└───────────────────────────────────────────────────────────────────────────┘
│                  │┌─ Pod: api-7f9c8d-x2k4p ───────────────────────────────── container: api ▾ ─┐
│                  ││ [1 Logs]  2 Describe  3 Events  4 YAML     ● follow  ○ wrap  ○ timestamps │
│                  ││ 14:02:11 INFO  GET /v1/orders 200 12ms                                    │
│                  ││ 14:02:12 INFO  GET /v1/orders/8812 200 31ms                               │
│                  ││ 14:02:14 WARN  slow query orders_by_user 1204ms                           │
│                  ││ 14:02:15 ERROR upstream payments: connection refused                      │
│                  ││ 14:02:15 INFO  retrying in 2s (attempt 2/5)                               │
│                  ││ 14:02:17 INFO  GET /healthz 200 0.4ms                                     │
└──────────────────┘└─ ▼ following · 1,204 lines ───────────────────────────────────────────────┘
 tab focus  j/k move  / filter  1-4 tabs  f follow  w wrap  c container  e exec  z zoom  ? help
```

### Why this arrangement
- **The sidebar runs the full height on the left, and the right side is split top and bottom** (pods above, details below). I avoided three columns because log lines are long. Putting the detail pane under the pod list gives logs about 75% of the terminal width instead of about 35%.
- **Navigation goes left to right and top to bottom:** namespace → pod → details. Selecting something in one pane immediately updates the pane after it, so you never have to press Enter just to look.
- **The header and footer are one line each.** The header shows context and cluster, because you need to see when you're in prod. The footer lists keybindings for whichever pane has focus.

## Sizing
| Region | Size |
|---|---|
| Sidebar | Fixed at 20 cols, or the longest namespace name + 6, capped at 28 |
| Pod list | 40% of the body height, minimum 5 rows |
| Detail pane | The remaining height, at least 8 rows |
| Header / footer | 1 row each |

### Responsive behavior
- **Under 100 cols:** drop the NODE column, then AGE. Truncate pod names in the middle (`worker-5b…-mm2lc`) so the unique hash suffix stays visible.
- **Under 80 cols:** collapse the sidebar. Show the namespace in the pod pane title and switch it with `n`, which opens a popup picker.
- **Under 24 rows:** show either the pod list or the detail pane, toggled with `Enter`/`Esc`.
- **`z` zoom:** expands the focused pane to the full body. This matters most for logs.

## Focus and interaction
- `Tab`/`Shift-Tab` (or `h`/`l`) moves focus. The focused pane gets an accent-colored border and the others are dimmed. Don't use a different border style for focus; it causes layout jitter.
- `/` filters whichever pane has focus. The filter text appears in that pane's top border, as in the mockup, and `Esc` clears it.
- **Pod list:** sort with `s`, which cycles through name, status, restarts, and age. Pods that aren't Ready, or are in CrashLoop or Error, sort to the top by default.
- **Detail tabs:** `1`–`4`. For multi-container pods, `c` picks the container, shown in the title as `container: api ▾`. Init containers go in the same picker.
- **Actions** (`e` exec, `d` delete, `p` port-forward): deleting a pod asks for confirmation in a modal that's centered over the body.

## Logs pane details
- **Follow mode is on by default.** Scrolling up pauses it and the bottom border changes to `‖ paused · 37 new ↓`. `G` or `f` resumes following.
- **Color by level:** ERROR in red, WARN in yellow. Highlighting the level token is enough; don't color the whole line.
- `/` inside logs highlights matches and `n`/`N` jumps between them. This is separate from the pod filter.
- `P` toggles `--previous` logs. When a pod is crash-looping, show a hint banner suggesting it.
- Keep a ring buffer of about 10k lines so long-running streams don't grow memory without limit.

## Status color (pod list)
| Color | Statuses |
|---|---|
| Green | Running with all containers Ready |
| Yellow | Pending, ContainerCreating, or not fully Ready |
| Red | CrashLoopBackOff, Error, ImagePullBackOff, OOMKilled |
| Dim gray | Completed, Terminating |

Mark restarts > 0 in yellow, and in red if the count is increasing.

## Empty, loading and error states
Each pane needs one, centered in the pane's body:
- **Loading:** a spinner and "Loading pods…"
- **Empty:** "No pods in `payments`" with a hint (`n` to switch namespace)
- **Error/RBAC:** "Forbidden: cannot list pods in kube-system". Show it inline; don't crash or open a modal.
- **Connection lost:** the header's `⟳ 2s ago` turns red and counts up.

If you tell me your stack (Ratatui, Bubble Tea, Textual, Ink…), I can turn this into the actual layout code with the constraint splits and the focus state machine.
