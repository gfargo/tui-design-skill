Remove both borders and give each fact one clear signal.

- **Border depth: 2 → 0.** A standalone list needs only a heading and whitespace. Keep one border only if it separates this list from another pane.
- **Success appears twice:** `[PASS]` and `(ok)`. Keep `PASS`; remove brackets and `(ok)`. If you use green too, that’s enough—no extra icon.
- **`>` on every row marks nothing.** Remove it. For an interactive list, highlight only the selected row with reverse video.
- **Chrome dominates the row:** `> [PASS] (ok)` occupies 13 of its 24 characters—54% before counting borders. Plain columns make the test name easier to find.

```text
Wide terminal                   60-column split
Tests                           Tests

Task              Status  Time  Task           Status  Time
build             PASS    2.1s  build          PASS    2.1s
lint              PASS    0.8s  lint           PASS    0.8s
test              FAIL    4.5s  test           FAIL    4.5s
```

Keep names in the normal foreground, dim timings, and optionally color only failures red. The status words preserve meaning without color.

At **80×24 and 60 columns**, keep this same single-pane layout, scroll long lists, and truncate long names while preserving status and time. Open full names and failure details on Enter. Below the width needed for those fields, hide timing first; show “terminal too small” only when the essential name and status can no longer fit.