Remove the nested frames and duplicate status signals. They give decoration the same visual weight as the build results.

Exactly what to cut:

- **All five boxes:** the outer frame and both boxes around each pane. Content currently sits **three borders deep**; six of the ten lines contain only framing.
- **`ok`, `fail`, `v`, and `x`:** each result is encoded four ways—status word, redundant word, symbol, and color. Keep just `PASS` or `FAIL`.
- **The brackets** around `[PASS]` and `[FAIL]`.
- **The `>` on every row:** three markers on three rows distinguish nothing. If this is an interactive list, mark only the selected row.
- **The right-hand pane’s `job: api` and `status: PASSED (v)`:** both repeat the list. Move its one unique value, duration, into the API row.
- **Full-row coloring:** use normal text for job names and successful results; color only `FAIL` red. The word preserves meaning without color.

At **72 columns**, use one borderless table. Unused space to the right stays blank; the supplied screen gives a duration only for API.

```text
 BUILD MONITOR

 Job       Status  Duration
 api       PASS      2m 10s
 web       PASS
 worker    FAIL
```

Bold the title, mute the column headings, and render `FAIL` in red. No additional icons are needed.

At **60 columns**, the same screen fits unchanged:

```text
 BUILD MONITOR

 Job       Status  Duration
 api       PASS      2m 10s
 web       PASS
 worker    FAIL
```

At **80×24**, keep this same single-pane layout. For longer job names, truncate the name within its column and expose the full name on drill-down. Below a proposed **32×7 minimum**, show `Terminal too small: need 32x7` instead of clipping the table.