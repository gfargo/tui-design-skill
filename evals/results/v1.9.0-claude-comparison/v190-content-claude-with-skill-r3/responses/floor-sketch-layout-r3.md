I'd build this as **three persistent panes at 120+ columns** (namespaces │ pods │ detail with Logs/Describe/Events tabs), the same arrangement lazydocker uses. Below 120 columns the sidebar turns into a namespace picker and the logs move **under** the pod list at full width. Below 80 columns it becomes a single-pane drill-down like k9s. The main thing driving the layout is that log lines are long and pod rows are short, so whenever width runs out, the logs get it.

## Wide (120+ cols, Pods focused)

```
 prod-eu ▸ payments ▸ api-7d9f4-x2k                                                                        synced 2s ago
 Namespaces         │ Pods 6                                             │ [Logs] Describe Events       api 1/2 ⋅ FOLLOW
 ────────────────── │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ ─────────────────────────────────────────────
   all          142 │ NAME              READY  STATUS      RESTARTS  AGE │ 14:02:11 GET /healthz 200 1ms
   default        3 │ api-7d9f4-x2k       2/2  Running            0   4d │ 14:02:12 POST /v1/charge 201 48ms
 > payments       6 │ api-7d9f4-q8m       2/2  Running            0   4d │ 14:02:12 POST /v1/charge 201 51ms
   ingress        4 │ worker-5c6b-9tz     0/1  CrashLoop…        14  12m │ 14:02:14 WARN stripe timeout, retry 2/5
   monitoring    18 │ worker-5c6b-k1p     1/1  Running            0  12m │ 14:02:15 POST /v1/charge 201 47ms
   kube-system   31 │ migrate-28713-x     0/1  Completed          0   2h │ 14:02:15 GET /healthz 200 1ms
                    │ redis-0             1/1  Running            0   9d │
 tab pane ⋅ / filter ⋅ l/d/e tab ⋅ s shell ⋅ z zoom ⋅ n namespace ⋅ ? help
```

- **Widths:** the sidebar takes about 18% (clamped to 18–28 columns), Pods gets at least 50, and Detail gets the rest with a minimum of 45. Any width past 120 goes to the logs.
- **Selection and focus:** the selected pod (`api-7d9f4-x2k`) is shown in reverse video, which can't be drawn here. The heavy `━` rule under "Pods" marks the focused pane, and the accent color reinforces it. Unfocused panes show their selection muted, which is what the `>` on `payments` stands for.
- **Header:** it carries the current location (cluster ▸ namespace ▸ pod) and whether the data is fresh. The logs' title row shows the container (`api 1/2`; `c` cycles containers) and the follow state.

## Standard (80×24): sidebar becomes a picker, logs stack below

```
 prod-eu ▸ payments ▸ api-7d9f4-x2k                                synced 2s ago
 Pods 6
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 NAME                            READY  STATUS            RESTARTS  AGE
 api-7d9f4-x2k                     2/2  Running                  0   4d
 api-7d9f4-q8m                     2/2  Running                  0   4d
 worker-5c6b-9tz                   0/1  CrashLoopBackOff        14  12m
 worker-5c6b-k1p                   1/1  Running                  0  12m
 migrate-28713-x                   0/1  Completed                0   2h
 redis-0                           1/1  Running                  0   9d
 [Logs] Describe Events                                         api 1/2 ⋅ FOLLOW
 ──────────────────────────────────────────────────────────────────────────────
 14:02:11 GET /healthz 200 1ms
 14:02:12 POST /v1/charge 201 48ms customer=c_81f2
 14:02:12 POST /v1/charge 201 51ms customer=c_09aa
 14:02:14 WARN stripe timeout after 5000ms, retry 2/5
 14:02:15 POST /v1/charge 201 47ms customer=c_77e1
 14:02:15 GET /healthz 200 1ms
 14:02:16 POST /v1/refund 200 33ms customer=c_81f2
 14:02:17 GET /healthz 200 1ms
 14:02:18 POST /v1/charge 201 52ms customer=c_3b0d
 14:02:19 GET /metrics 200 4ms
 14:02:20 POST /v1/charge 201 49ms customer=c_9f12
 tab pane ⋅ / filter ⋅ n namespace ⋅ l/d/e tab ⋅ s shell ⋅ z zoom ⋅ ? help
```

- **Why stacked:** the usual 80-column fallback puts list and detail side by side at 40 columns each, which would truncate almost every log line. Stacking gives the logs 78 columns.
- **Split:** 6 pod rows and 11 log rows. The list scrolls and shows its position in the title (`Pods 3/48`). `z` zooms whichever pane is focused to full height.
- **Namespaces:** the namespace stays visible in the header. `n` opens an fzf-style picker overlay with the same per-namespace pod counts.

## Floor (60 cols): single pane, drill-down

```
 prod-eu ▸ payments                            synced 2s ago
 Pods 6
 NAME                      READY  STATUS            AGE
 api-7d9f4-x2k               2/2  Running            4d
 api-7d9f4-q8m               2/2  Running            4d
 worker-5c6b-9tz             0/1  CrashLoopBackOff  12m
 worker-5c6b-k1p             1/1  Running           12m
 migrate-28713-x             0/1  Completed          2h
 redis-0                     1/1  Running            9d

 enter open ⋅ / filter ⋅ n namespace ⋅ s shell ⋅ ? help
```

Pressing Enter opens the detail full-screen, and Esc goes back:

```
 prod-eu ▸ payments ▸ worker-5c6b-9tz          synced 2s ago
 [Logs] Describe Events                      PAUSED ▾ 37 new
 ──────────────────────────────────────────────────────────
 14:01:58 starting worker queue=charges
 14:01:59 connected redis-0:6379
 14:02:03 ERROR stripe: 401 invalid api key
 14:02:03 exit code 1
 ── restart 14 at 14:02:14 ──
 14:02:15 starting worker queue=charges

 esc back ⋅ G follow ⋅ / search ⋅ p previous ⋅ ? help
```

## Breakpoints and the floor test

| Size | Layout | What gives way |
|---|---|---|
| ≥120 cols and ≥20 rows | Three panes | Nothing |
| 80–119 cols, ≥20 rows | Pods on top (~40%), detail below (~60%) | Sidebar becomes the `n` picker |
| 50–79 cols, **or fewer than 20 rows at any width** | Single-pane drill-down | RESTARTS column (still in Describe); footer hints drop from the right, `? help` always stays |
| Below 50×12 | `terminal too small: need 50×12 (now 44×10)` with `q` and Ctrl+C still working | Everything |

- **Height rule:** a wide but short tmux pane can't fit two stacked panes, so height has its own breakpoint.
- **Column priority:** NAME, STATUS, READY, AGE, RESTARTS, then NODE/IP (wide only). Pod names are truncated in the **middle** (`worker-5c6b…k1pqz`) because both the prefix and the hash suffix identify the pod.

## Behavior that shapes the layout

- **Logs follow the selection, with a delay:** moving the cursor in Pods switches the log stream after about 200 ms of idle. Cancel the old stream first, and start from the tail (around 500 lines), not the full history. Moving the cursor in the sidebar refreshes the pod list the same way. Choosing "all" adds a NAMESPACE column, and that's the only time it appears.
- **Follow mode:** logs follow by default. Any upward scroll pauses and shows `PAUSED ▾ N new`, and `G` or `F` resumes following. Other keys:
  - `p` shows the previous container's logs, which is the key you need for CrashLoopBackOff.
  - `w` toggles wrapping.
  - `t` toggles timestamps.
  - A restart is drawn as one divider line in the log.
- **Live data:** track the selected pod by UID, not by row position. When a rollout deletes the selected pod, select its nearest neighbor. If the logs pane is focused or zoomed, though, keep showing the dead pod's logs with `pod deleted 12s ago` until the user leaves. Otherwise a rollout would yank the logs out from under them mid-read.
- **Keys:**
  - Tab / Shift+Tab move between panes (three panes is too few to need number jumps).
  - `l` `d` `e` jump straight to Logs, Describe and Events; `[` `]` cycle tabs.
  - `/` filters in lists and searches in logs.
  - `s` hands the terminal to `kubectl exec`. Use the framework's suspend/resume support, then reload and redraw when it returns.
  - Esc steps back one level and never quits. `q` quits only from the top level. Ctrl+C cancels running work first, then quits.

## States to design

| State | Shown as |
|---|---|
| Connecting | The layout is drawn immediately, with `connecting to prod-eu… 3s` and `Esc cancel` |
| Empty namespace | `No pods in "payments".` plus `n change namespace` |
| Listing namespaces forbidden (RBAC) | Partial: the sidebar says `! can't list namespaces`, and `n` accepts a typed name |
| Container not started | The log pane shows `Waiting: ContainerCreating` instead of a blank pane |
| API unreachable | The last data stays visible, dimmed, with `STALE 2m ⋅ reconnecting (3) ⋅ r retry` in the header |
| Error | `✗ Forbidden: pods/log in payments`. It stays until dismissed, then moves to a message log |

## Clutter audit (of this design)

- **Border nesting depth:** 0. There are no boxes, just one `│` between columns and a rule under each pane title. The rule doubles as the focus cue (heavy when focused, light otherwise), so it earns its space.
- **Signals for pod status:** the STATUS word plus a color, and only for unusual states: CrashLoopBackOff and Error in red, Pending in yellow, Completed dimmed. Running gets no color. READY is never colored, because that would be a third signal for the same fact.
- **Markers on every row:** none. Only the selected row is highlighted.
- **Chrome:** 7 of 24 rows at 80×24 (header, two titles, two rules, column header, footer). That's about 29%, and the content area is all data.
- **What I left out:**
  - an outer frame
  - a box around each pane
  - a ✓/✗ icon column that would repeat STATUS
  - full ISO timestamps and a pod-name prefix on each log line (the header already names the pod)
  - "press ? for help" text inside panes

**Stack:** none was named, and the layout doesn't depend on one. If you're starting fresh, Go with Bubble Tea is a good fit: client-go is native Go, and k9s and lazydocker show the approach works. Whatever you pick, add golden-frame tests at 120×40, 80×24, 60×20 and 50×12, plus unit tests for keeping the selection by UID and for pausing and resuming follow mode.

I can go further on any part of this, such as the namespace picker overlay, the Describe tab, or a Bubble Tea or Ratatui skeleton.
