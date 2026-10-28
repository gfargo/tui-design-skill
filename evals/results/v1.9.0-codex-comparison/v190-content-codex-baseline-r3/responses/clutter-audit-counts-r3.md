Give each element one job: `>` marks selection, a status icon shows the result, and alignment separates the name from timing. `[PASS]` and `(ok)` repeat the same information.

```text
Tests                         12 passed

  ✓ lint                         0.4s
› ✓ build                        2.1s
  ✕ integration                  3.8s
  ✓ unit                         0.9s
```

- Remove both borders if spacing makes the list clear; keep one if it separates the list from other panels.
- Use a subtle background for the selected row, or keep `›` if backgrounds aren’t available.
- Dim timings and right-align them.
- Reserve strong color for failures and the active selection.
- Put failure details below the list or in a detail pane.

Start by removing `(ok)` and the inner border. Those two changes should make it noticeably calmer.