Use three panes: a narrow namespace sidebar, a pod list above, and pod details with logs below. This keeps log lines wide enough to read.

```text
 kpods   context: staging-us-east                     / search   ? help
┌─ Namespaces ─────┬─ Pods · payments ───────────────────────────────────┐
│ / filter        │ NAME                      READY  STATUS    RESTARTS │
│                 │ api-7d9f6b-x2k9p           2/2    Running          0 │
│   All namespaces│▶api-7d9f6b-m8q4r           1/2    CrashLoop        5 │
│   default       │ worker-5c8b9-n3v7t        1/1    Running          0 │
│   kube-system   │ scheduler-6f2a1-p9w2s     0/1    Pending          0 │
│ ▶ payments    12│                                                    │
│   monitoring   8├─ api-7d9f6b-m8q4r ──────────────────────────────────┤
│   ingress      3│ Logs  Overview  Events  YAML                       │
│                 │ container: api ▾   previous: off   timestamps: on   │
│                 │────────────────────────────────────────────────────│
│                 │ 14:32:08 INFO  Starting server on :8080             │
│                 │ 14:32:08 INFO  Connecting to database               │
│                 │ 14:32:13 ERROR Connection timed out                 │
│                 │ 14:32:13 ERROR Process exited with code 1           │
│                 │                                                    │
│                 │                                      Following ↓   │
└─────────────────┴────────────────────────────────────────────────────┘
 Tab pane   j/k move   Enter open   / filter   f follow   z zoom   q quit
```

- **Sizing:** Sidebar 20–24 columns; remaining width goes to pods and details. Start with a 40/60 vertical split and allow resizing.
- **Focus:** Give the active pane a bright border and title. Preserve a subdued selection highlight in inactive panes so the selected namespace and pod stay visible.
- **Pod list:** Prioritize name, readiness, status, and restarts. Add age and node when width permits. Use stable ordering by default so refreshes don’t move the selection.
- **Details:** Default to Logs, with Overview, Events, and YAML as tabs. Keep container selection and log controls visible above the output.
- **Logs:** Follow automatically until the user scrolls upward; then show “Paused · N new lines.” Press `f` to resume. Support `/` search, timestamps, wrapping, and previous-container logs.
- **Color:** Use muted text for metadata, green for healthy, amber for pending, and red for failures. Always show status text alongside color.

Use `Tab` / `Shift+Tab` to switch panes, arrow keys or `j/k` to navigate, and `z` to maximize the focused pane. Namespace changes update the pod list; moving through pods updates details after a short debounce.

On narrow terminals, collapse namespaces into a selector in the header. On very small terminals, show one pane at a time with a breadcrumb: `payments › api-7d9f6b-m8q4r › Logs`.