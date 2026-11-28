Remove all five boxes and collapse the detail pane. The noise comes from three layers of borders and the same status repeated four ways: `[PASS]`, `ok`, `v`, and green.

Make these exact cuts:

- Delete the outer frame, both panel frames, and both inner frames: border depth **3 → 0**.
- Delete `ok` / `fail`, `v` / `x`, and the brackets around `PASS` / `FAIL`. Keep the status words.
- Remove green from successful rows. Color only `FAIL` red, keeping everything else neutral.
- Delete the repeated `job: api` and `status: PASSED (v)` fields. Preserve the duration.
- Delete the `>` on every row. If this is interactive, mark only the selected row; the sketch assumes `api` is selected.

Seven of the ten original lines contain no job data. Borders and repeated labels dominate the screen.

At **72 columns**, with unused space left blank:

```text
 BUILD MONITOR

   Job       Status
 > api       PASS
   web       PASS
   worker    FAIL

 Duration: 2m 10s
```

`Duration` follows the selected job. In the actual terminal, use reverse video on the selected row instead of `>`; the marker here makes selection visible in plain text. Only the word `FAIL` is red, so status remains readable without color.

At **60 columns**, the same layout fits:

```text
 BUILD MONITOR

   Job       Status
 > api       PASS
   web       PASS
   worker    FAIL

 Duration: 2m 10s
```

At **80×24**, keep this single pane. Longer job names truncate before the status column; full names and additional details open on Enter, with Esc returning. A reasonable minimum for this layout is **32×8**; below that, show `Terminal too small: need 32x8`.