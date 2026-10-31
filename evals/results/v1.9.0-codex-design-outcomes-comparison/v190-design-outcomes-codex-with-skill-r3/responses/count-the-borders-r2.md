Remove all five boxes and consolidate the details into the job list. The busyness comes from repeated boundaries and repeated status signals.

Exactly what to cut:

- **All borders:** the outer frame and both layers around each pane. Content sits three borders deep.
- **`ok`, `fail`, `v`, and `x`:** each status currently appears four ways—word, repeated word, symbol, and color. Keep just `PASS` or `FAIL`, with optional color.
- **The brackets around status words:** `[PASS]` becomes `PASS`.
- **The `>` on every row:** three identical markers distinguish nothing. Keep one only on the selected job.
- **The right-hand detail pane:** `job: api` and `status: PASSED (v)` repeat the selected row. Move its only new information, duration, into a column.
- **Full-row green/red:** color only the status word. Keep job names and durations in the normal foreground.

Six of your ten screen rows contain only borders and spacing. That framing gets more vertical space than the data.

At **72 columns**, with unused space left blank:

```text
 BUILD MONITOR

   Job       Status  Duration
 > api       PASS    2m 10s
   web       PASS
   worker    FAIL
```

Here `>` means **api is selected**. Only `PASS` is green and `FAIL` red; the words preserve meaning without color. Blank durations mean the supplied screen didn’t provide those values.

At **60 columns**, use the same single-pane layout:

```text
 BUILD MONITOR

   Job       Status  Duration
 > api       PASS    2m 10s
   web       PASS
   worker    FAIL
```

At **80×24**, keep this layout too; extra width doesn’t justify restoring duplicate details. For longer names, truncate the job column before sacrificing status. A compact version can fit **32×6**; below that, show `Terminal too small: need 32x6`.