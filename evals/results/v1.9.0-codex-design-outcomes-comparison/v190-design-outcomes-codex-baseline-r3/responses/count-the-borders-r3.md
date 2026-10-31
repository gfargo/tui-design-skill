The busyness comes from repetition: nested boxes, four status signals per row, and a detail panel repeating the selected job.

Remove:

- All box borders, including the outer frame.
- The brackets around `PASS` and `FAIL`.
- `ok`, `fail`, `v`, and `x`—they repeat the status.
- The `>` on unselected rows; keep one for the selection.
- The right panel. Move its duration onto the `api` row.

Keep green PASS and red FAIL text, without coloring the whole row.

```text
BUILD MONITOR

  JOB          STATUS   DURATION
> api          PASS     2m 10s
  web          PASS
  worker       FAIL
```

This fits comfortably within 72 columns. Each remaining element has one job: the arrow marks selection, the status reports the result, and the duration adds information.