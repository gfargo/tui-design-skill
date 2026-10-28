The project directory is empty, so this design doesn't assume a framework. It works the same in Bubble Tea, Ratatui or Textual.

## Layout (shown at 100×20)

```
 cluster: prod-us-east-1   user: admin                                       synced 2s ago   ? help 
┌ Namespaces ───────┐┌ Pods · payments (12) ───────────────────────────────────────────────────────┐
│  All          148 ││ NAME                          READY  STATUS            RESTARTS  AGE        │
│  default        3 ││ api-7d9f8c6b-x2kqp            2/2    Running                  0  3d         │
│▶ payments      12 ││▶worker-5b6c7d-mm9zt           0/1    CrashLoopBackOff        14  2h         │
│  ingress-nginx  4 ││ worker-5b6c7d-pq1rs           1/1    Running                  0  2h         │
│  kube-system   22 ││ db-migrate-28391-abcde        0/1    Completed                0  1d         │
│  monitoring    18!││ api-7d9f8c6b-v8wnt            0/2    Pending                  0  12s        │
│                   │└─────────────────────────────────────────────────────────────────────────────┘
│                   │┌ [Logs]  Describe  Events  YAML ────────────────────────── container: worker ─┐
│                   ││ worker-5b6c7d-mm9zt  node ip-10-0-3-41  IP 10.0.3.118  restarts 14          │
│                   ││ last state: Terminated (Error, exit 2) 41s ago                              │
│                   │├─────────────────────────────────────────────────────────────────────────────┤
│                   ││ 14:02:11 INFO  starting worker pool size=8                                  │
│                   ││ 14:02:11 INFO  connecting to redis-master.cache:6379                        │
│                   ││ 14:02:16 ERROR dial tcp 10.0.7.12:6379: connect: refused                    │
│                   ││ 14:02:21 WARN  retrying in 5s (attempt 3/3)                                 │
│                   ││ 14:02:26 FATAL giving up: redis unavailable                                 │
└───────────────────┘└─────────────────────────────────────────── FOLLOW · wrap off · 1,204 lines ─┘
 PODS  j/k move  enter logs  / filter  tab next pane  z zoom  ? help  q quit
```

## Why it's arranged this way

The pod list sits **above** the detail pane instead of in a third column. Three side-by-side columns would squeeze the logs into about 40 columns, and logs are the widest, most-read content. Stacking gives log lines the full right-hand width. The pod list only needs to show 6–15 rows at a time.

## Sizing rules

| Region | Size |
|---|---|
| Header / footer | 1 row each, always visible |
| Namespace sidebar | Fixed width: longest name + count, clamped between 18 and 28 columns |
| Pod list | Pod count + 3 rows, capped at 40% of the body height. A 4-pod namespace doesn't waste half the screen |
| Detail pane | Everything left over |

**Breakpoints:**
- **≥ 120 columns:** add NODE and IP columns to the pod list.
- **< 100 columns:** hide the sidebar. The namespace moves into the header (`ns: payments ▸`), and `n` opens it as an overlay picker with fuzzy search.
- **< 24 rows:** the pod list shrinks to 5 rows and the 2-line pod summary collapses to 1 line.
- **`z` (zoom):** the focused pane goes full screen, which is mostly useful for logs. Press `z` or `Esc` to go back.

## Focus and navigation

- Only one pane has focus at a time. Show it with a bright border and bold title, and dim the other borders. The footer's first word (e.g. `PODS`) names the focused pane, and the key hints change to match it.
- `Tab` / `Shift-Tab` cycle through the panes, and `h` / `l` move left and right. In the sidebar and pod list, `j` / `k` move the cursor and `Enter` selects and moves focus one pane to the right.
- **The selection drives the panes to its right.** Moving the cursor in the pod list updates the detail pane after about 150 ms. That way, scrolling quickly doesn't open a log stream for every pod you pass.
- `/` filters whichever list has focus, and the filter shows in that pane's title: `Pods · payments (3/12) /worker`.

## Detail pane

- **Tabs:** Logs | Describe | Events | YAML. Switch with `1`–`4` or `[` / `]`. Logs is the default tab.
- **Summary header:** 2 rows that answer "why is this broken?" without leaving the logs: node, IP, restarts, and the last termination reason and exit code.
- **Container picker:** shown in the top border on the right, only for pods with more than one container. Press `c` to cycle containers. Init containers get an `init:` prefix.
- **Follow mode:** on by default. Scrolling up pauses it automatically, and the indicator changes to `PAUSED · 37 new`. `G` or `f` turns it back on. This matters more than anything else on this pane: without it, people lose their place while reading a stack trace.
- **Log toggles:** `w` wrap, `t` timestamps, `p` previous container's logs (essential for CrashLoopBackOff), `/` search within logs, `n` / `N` next and previous match.
- Logs are kept in a capped ring buffer (around 10k lines), and the bottom border shows the line count.

## Visual language

- **Status colors:** Running = green, Pending/ContainerCreating = yellow, CrashLoop/Error/OOMKilled = red, Completed = dim gray. The status text always stays visible, so color isn't the only signal.
- **Readiness:** a READY value below its total (e.g. `0/1`) is shown in yellow even when the status is Running. This catches pods that are running but failing their readiness probe.
- **Namespace alerts:** a namespace containing an unhealthy pod gets a `!` in the sidebar, so problems show up without opening each namespace.
- **Log levels:** color only the level token (ERROR red, WARN yellow). Coloring the whole line makes the logs hard to read.

## States to design for

- **Loading:** a spinner in the pane title. Keep showing the stale data dimmed rather than blanking the pane.
- **Empty:** a centered message in the pane, e.g. `No pods in payments` with a hint like `n: switch namespace`.
- **No permission (RBAC):** show `forbidden: cannot list pods in kube-system` inside the pane, not as a crash or a toast.
- **Pod deleted while you're viewing it:** freeze the logs, change the title to `worker-… (deleted)` in red, and keep the content readable.
- **Lost connection to the API server:** the header's `synced 2s ago` turns yellow, then red, as time passes.

If you tell me which framework you're using (Bubble Tea, Ratatui, Textual, Ink), I can scaffold this layout with the sizing rules and focus handling in place.
