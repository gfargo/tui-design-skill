Give each row one status cue, and let spacing do the grouping.

- Replace `[PASS] (ok)` with a single `✓` or `PASS`.
- Show `>` only on the selected row.
- Right-align durations in a muted color.
- Remove both borders; use a heading and whitespace. Keep one border only if the panel needs separation from adjacent content.

```text
Tests                         12 passed

  ✓ lint                         0.4s
> ✓ build                        2.1s
  ✓ unit tests                   1.3s
```

Use a subtle background for selection if available, so you can drop `>` too. Reserve stronger color and extra detail for failures.