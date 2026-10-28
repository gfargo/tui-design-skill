I recommend a **full-screen app with the namespace sidebar on the left, and the pod list stacked above the detail/logs pane on the right**. The three panes don't sit side by side. The layout collapses into a k9s-style drill-down as the terminal gets smaller.

The reason for stacking: log lines are the widest content in the app, often 120+ characters. Three columns side by side at 120 cols would leave logs about 45 columns, so nearly every line would get cut off. Stacking gives both the pod table and the logs about 97 columns. The cost is fewer visible pod rows, and `z` (zoom) handles that.

## Wide (≥110 cols, ≥30 rows)

```
 prod-us-1 / payments / pods / api-7d9f-x2k                                                     live ⋅ updated 2s ago
 Namespaces        12 | ▸ Pods                                                                                     2/14
  default             | NAME                              READY  STATUS            RESTARTS   AGE  NODE
  ingress-nginx       | api-7d9f-q8m                      1/1    Running                  0    4d  node-a3
  kube-system         |>api-7d9f-x2k                      1/1    Running                  0    4d  node-b1
  monitoring          | worker-5c6b-zz1                   0/1    CrashLoopBackOff        12    2h  node-a3
~ payments            | migrate-28411030-hk2p4            0/1    Completed                0    1d  node-c2
  staging         ! 2 | web-6f8d4-9tq                     1/1    Running                  0    4d  node-b1
  tools               |-- api-7d9f-x2k -- [Logs]  Describe  Events ------------------------- api 1/2 ⋅ FOLLOW --
                      | 14:02:11  info  GET /v1/charges 200 41ms req=8f2c user=u_1932
                      | 14:02:11  info  GET /healthz 200 1ms
                      | 14:02:12  info  POST /v1/refunds 201 88ms req=8f31 user=u_2207
                      | 14:02:14  warn  slow query charges_by_customer took 1204ms
                      | 14:02:15  error stripe webhook signature mismatch evt=evt_3PqZ…
 tab pane ⋅ / filter ⋅ enter logs ⋅ d describe ⋅ s shell ⋅ n namespace ⋅ p previous logs ⋅ z zoom ⋅ ? help
```

How to read the sketch: `>` is the reverse-video selected row in the focused pane, and `~` is the dimmer selection in an unfocused pane. These are sketch notation only. The real UI draws no glyph at the start of a row.

- **Header:** shows where you are (cluster / namespace / resource / pod) and how fresh the data is.
- **Sidebar:** 20–28 cols. It shows `! 2` only on namespaces with unhealthy pods, so a warning marker means something.
- **Pods:** 40% of the height, at least 6 rows. Columns in priority order are NAME, STATUS, READY, RESTARTS, AGE, NODE, and they drop from the right as the pane narrows. Names that don't fit end in `…`.
- **Detail:** the rest of the height. The title sits inside the dividing line between pods and detail, so it costs no extra row. Tabs switch with `l` / `d` / `e` or `[` / `]`. `c` cycles containers (`api 1/2`). The right end of that line shows `FOLLOW`, or `PAUSED ▾ 37 new` when you've scrolled away from the bottom.
- **Logs:** show only `HH:MM:SS`, not the full date on every line (`t` toggles timestamps). Long lines are cut off by default, since most pod logs are JSON or structured; `w` wraps them.

## Floor: 60 columns (and 80×24), single-pane drill-down

```
 prod-us-1 / payments / pods                     live 2s
 Pods                                               2/14
 NAME                        READY  STATUS            RST
>api-7d9f-x2k                1/1    Running             0
 worker-5c6b-zz1             0/1    CrashLoopBackOff   12
 migrate-28411030-hk2p4      0/1    Completed           0
 web-6f8d4-9tq               1/1    Running             0
 enter logs ⋅ / filter ⋅ n namespace ⋅ q quit ⋅ ? help

        ── enter ──▶

 prod-us-1 / payments / api-7d9f-x2k              FOLLOW
 [Logs]  Describe  Events                        api 1/2
 14:02:11  info  GET /v1/charges 200 41ms req=8f2c use…
 14:02:12  info  POST /v1/refunds 201 88ms req=8f31 u…
 esc back ⋅ / search ⋅ F follow ⋅ w wrap ⋅ ? help
```

## Breakpoints: two independent axes

| Condition | Behavior |
|---|---|
| width ≥ 110 | Sidebar is visible |
| width < 110 | Sidebar hides. `n` opens a namespace picker you can type to filter, and the header still shows the namespace |
| height ≥ 30 | Pods sit above the detail pane, and the detail follows the selected pod |
| height < 30 | Pods take the full screen. `Enter` opens the detail full-screen and `Esc` goes back |
| width < 60 | RESTARTS, AGE and NODE drop. Name gets 24+ cols and status keeps 16 |
| below 50×12 | Shows `terminal too small: need 50x12`. `q` and `Ctrl+C` still work |

So at **80×24** you get the 60-column layout with all the columns, and in a **60-column tmux split** you get the sketch above. `z` zooms the detail pane to full screen at any size.

## Interaction decisions that matter for this app

- **Focus:** `Tab` cycles the three panes. The focused pane gets a `▸` before its title plus the accent color. Only the focused pane shows the reverse-video selection, so focus is still visible without color.
- **Keep the selection in place:** track the selected pod by UID, not by row number. When a pod is deleted, select the next pod, not the first one. Don't re-sort on refresh, and don't scroll the list out from under the cursor.
- **Wait before switching log streams:** while the user holds `j`, wait about 150 ms before opening the selected pod's log stream, and cancel the old stream. Otherwise scrolling through 20 pods opens 20 streams.
- **Follow mode:** logs open following the newest lines. Any upward scroll pauses following and shows a count of new lines; `G` or `F` resumes. Keep a capped buffer (about 50k lines) and say when old lines were dropped.
- **`p` shows the previous container's logs:** this is the one place logs become useful for a `CrashLoopBackOff` pod. Mark it clearly with `PREVIOUS (exited 2m ago)`.
- **`s` shell:** this hands the terminal to `kubectl exec`. Pause the UI, restore the terminal, run the command, then come back, refresh the pod data, and redraw everything.
- **Esc order:** cancel a running load, then close any overlay, then clear the filter, then go back a level. Esc never quits. `q` quits at the top level, and `Ctrl+C` quits from anywhere.

## States to design up front

- **Loading:** the layout draws immediately. Old rows stay visible during a refresh, with `loading… 3s  esc cancel` in the pane title.
- **Empty:** `No pods in "staging"  ⋅  n change namespace`.
- **No logs yet:** `container api is waiting (ContainerCreating)` instead of a blank pane.
- **Forbidden (no permission):** the namespace stays in the sidebar, dimmed, with `forbidden`. It's never just hidden.
- **Lost connection:** the last known data stays on screen, dimmed, with `STALE 2m ⋅ reconnecting (3) ⋅ r retry`.
- **Pod deleted while viewing its logs:** the logs freeze, the title shows `pod deleted`, and the lines stay readable.

## Clutter check of this layout

- **Borders:** no outer frame and no boxes inside boxes, so no content sits more than zero borders deep. There's one vertical rule and one horizontal rule, and the horizontal rule also holds the detail title.
- **Status:** each status uses two signals, the word (`CrashLoopBackOff`) and red. `Completed` is dimmed. There are no status icons on top of the word.
- **Markers:** nothing appears on every row. `! 2` shows up only on namespaces that have problems.
- **Chrome:** four rows (header, pods title, divider, footer) plus a one-column rule. Log lines lose 10 columns to the time, not 25 to a full timestamp.

On the stack: I've kept this framework-neutral. If you haven't picked one, Go with Bubble Tea is the natural fit because client-go (the Kubernetes API library) is Go. Tell me your stack and I'll turn this into code.
