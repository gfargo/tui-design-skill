# Kubernetes pod browser: layout design

**Recommendation:** use a full-screen app on the alternate screen. On wide terminals, show three persistent panes (namespaces, pods, detail). As the terminal gets narrower, switch to a k9s-style drill-down: pods, then Enter for logs, then Esc to go back. Namespaces are the least-used pane, so the sidebar folds away first. Logs are what users come for, so the detail pane survives longer.

Ecosystem: none was named. I'd pick **Go + Bubble Tea**, because `client-go` and its watch/informer machinery are native there. Everything below is framework-agnostic.

## Dominant loop and core actions

Loop: **pick a namespace → scan pods for trouble → read that pod's logs**, repeated often. Namespace changes are rare compared with pod and log work.

Common actions: move (`j/k`), filter pods (`/`), open or focus logs (`Enter`/`l`), describe (`d`), shell (`s`), switch namespace (`n` or focus `1`), follow/pause logs (`f`/`G`), and previous-container logs for crash loops (`p`).

## Wide (≥130 cols)

```
 prod-eu / staging / pods                                                                            ✓ synced 3s ago
┌ 1 Namespaces ────┐┏ 2 Pods 48 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓┌ 3 api-7d9f-x2k9p/app ────────────────────────────┐
│  default         │┃ NAME                RDY  STATUS     RST AGE┃│ [Logs]  Describe  Events               following │
│  kube-system     │┃>api-7d9f-x2k9p      1/1  Running      0  4d┃│ 14:02:11 GET /health 200 2ms                     │
│  monitoring      │┃ api-7d9f-q8m2v      1/1  Running      0  4d┃│ 14:02:12 GET /v1/orders 200 41ms                 │
│  payments        │┃ worker-5cf8…-hj7tq  0/1  CrashLoop   14  2h┃│ 14:02:12 WARN slow query orders_by_user 812ms    │
│> staging         │┃ migrate-29p4k       0/1  Pending      0 12s┃│ 14:02:13 GET /v1/orders/9921 404 3ms             │
│                  │┃ redis-0             1/1  Running      2 31d┃│ 14:02:14 GET /health 200 1ms                     │
│                  │┃                                            ┃│                                                  │
└──────────────────┘┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛└──────────────────────────────────────────────────┘
 j/k move ⋅ enter logs ⋅ / filter ⋅ d describe ⋅ s shell ⋅ space pause ⋅ ? help
```

How to read the sketch: `>` marks the selected row. When rendered, that row is reverse video in the focused pane and plain bold in unfocused panes. A heavy border shows which pane has focus.

- **Header:** shows where you are (`context / namespace / view`) and how fresh the data is. That one line replaces any titles inside the panes.
- **Sidebar:** 20 columns (clamped to 16–28). Moving the selection *is* switching namespace, so it needs no separate "active" marker. Debounce the switch by about 150 ms.
- **Pod list:** at least 40 columns. Column priority as width shrinks: NAME, STATUS, RST, AGE, RDY, then NODE/IP (only at 160+). Truncate pod names **in the middle** (`worker-5cf8…-hj7tq`), because the hash suffix is what tells replicas apart. Use short STATUS words (`CrashLoop`) and show the full reason in Describe.
- **Detail:** fills the rest of the width, with a minimum of 50. Switch tabs with `[`/`]`, since `1`–`3` are taken by pane jumps. The title shows `pod/container`, and `c` cycles containers. `z` zooms the detail pane to full screen at any width.

## Breakpoint ladder

| Width | Layout |
|---|---|
| ≥130 | All three panes, as above |
| 100–129 | The sidebar becomes an `n` namespace picker (fzf-style overlay). The list takes ~45% and the detail ~55%. |
| 48–99 | One pane with drill-down: pod list → `Enter` → full-screen logs → `Esc` back |
| <48×12 | A too-small message |

I didn't keep a split at 80 columns because logs in a 40-column pane wrap or truncate badly. A full-width log view is more useful than seeing both at once.

## 80×24: drill-down, no borders (depth 0)

```
 prod-eu / staging / pods  48                                  ✓ synced 3s ago
 NAME                          READY  STATUS      RESTARTS  AGE
>api-7d9f-x2k9p                1/1    Running            0  4d
 api-7d9f-q8m2v                1/1    Running            0  4d
 worker-5cf86b7d4-hj7tq        0/1    CrashLoop         14  2h
 migrate-29p4k                 0/1    Pending            0  12s
 enter logs ⋅ / filter ⋅ n namespace ⋅ d describe ⋅ s shell ⋅ ? help
```

```
 prod-eu / staging / api-7d9f-x2k9p / logs (app)              paused  ▾ 37 new
 14:02:11 GET /health 200 2ms
 14:02:12 GET /v1/orders 200 41ms
 G follow ⋅ / search ⋅ w wrap ⋅ p previous ⋅ c container ⋅ esc back ⋅ ? help
```

## 60 columns (tmux split)

```
 staging / pods 48                          ✓ 3s
 NAME                       STATUS        RST
>api-7d9f-x2k9p             Running         0
 worker-5cf86b7d4-hj7tq     CrashLoop      14
 enter logs ⋅ / filter ⋅ n ns ⋅ ? help
```

AGE and READY drop out here, and Describe still has every field. The footer keeps dropping hints from the right but always keeps `? help`. Below 48×12 the app shows `terminal too small: need 48×12 (now 41×10)`, and `q` and `Ctrl+C` still work.

## States to design up front

| State | What the user sees |
|---|---|
| Loading | Draw the frame immediately. Show a spinner after ~150 ms in the pane that is loading, with elapsed time after 2 s. `Esc` cancels. |
| Empty namespace | `No pods in "staging".  n change namespace` |
| RBAC forbidden | In the sidebar: `kube-system  (no access)`, dimmed. Selecting it says `✗ forbidden: cannot list pods`. Never show a blank list. |
| Pending / ContainerCreating | Logs pane: `Waiting for container to start…` instead of an empty pane |
| CrashLoop | Logs pane offers `p previous container logs`. That's usually what the user needs. |
| Pod deleted while viewing | Keep the logs, and mark the title `(pod gone 12s ago)` |
| API unreachable | Keep the last rows, dimmed, with `STALE 40s  reconnecting (3)  r retry` in the header |

## Interaction rules that shape the layout

- **Focus:** `Tab`/`Shift+Tab` or `1`/`2`/`3`. Focus shows through the heavy border plus a bold title, and the accent color only reinforces it. The footer hints change with the focused pane.
- **Live list:** track the selection by **pod UID**, not by row index. If the selected pod disappears, select the nearest neighbor. Don't re-sort on refresh. `space` pauses list updates and shows `PAUSED  +5 changes`.
- **Log streams:** wait ~250 ms after the selection settles before opening a stream, and cancel the previous one. Otherwise, holding `j` opens 40 log streams. Use a ring buffer of about 50k lines and say when old lines are dropped.
- **Follow mode:** logs follow by default. Any upward scroll pauses following and shows `▾ N new`. `G` or `f` resumes. `w` toggles wrapping.
- **Esc order:** cancel a load → close a modal → clear the filter → back out of a drill-down → do nothing. `Esc` never quits. `q` backs out one level and quits only at the root.
- **Room to grow:** if you later add services and deployments, add a `:` command mode (`:svc`, `:deploy`) rather than more panes.

## Clutter audit of this design

- **Border nesting depth: 1** at wide sizes and 0 at single-pane sizes. Don't put a frame around the whole app, and don't box the log text inside the detail pane.
- **Pod status:** two signals, the word plus its color (Running green, CrashLoop red, Pending yellow). Don't add a status icon or a row marker as well.
- **Always-on markers: none.** No per-row pod icon and no pod count per namespace; counting pods in every namespace also costs one API list call per namespace.
- **Chrome:** one header row, one footer row, and pane titles that carry data (the counts and the `pod/container` name). Log lines show `HH:MM:SS`, not a full RFC 3339 timestamp, because the date never changes within a session.

## Test the layout at pinned sizes

Use golden frames at 130×40, 110×30, 80×24, 60×20 and 47×11 (the too-small state). Also unit-test these state transitions:

- the selected UID surviving a refresh;
- the debounced log stream being cancelled when the selection moves;
- follow mode pausing and resuming;
- the RBAC-forbidden and stale states.
