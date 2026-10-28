Give each row one status cue, and let spacing do the grouping.

```text
Tests                         8 passed · 1 failed

  ✓ build                         2.1s
  ✓ lint                          0.4s
› ✗ integration                   3.8s
  ✓ unit                          1.2s
```

- Replace `[PASS] (ok)` with a single `✓` or `PASS`.
- Show `›` only on the selected row, or use a subtle background highlight.
- Remove both nested borders. Use a heading and whitespace; keep one border only if the panel needs separation from nearby content.
- Right-align durations in a muted color.
- Reserve strong color for failures and selection. Keep passing rows quiet.

The test name should be the first thing your eye finds; status and timing should support it.