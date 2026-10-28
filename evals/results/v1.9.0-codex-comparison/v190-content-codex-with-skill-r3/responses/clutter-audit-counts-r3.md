Remove both boxes and give each row one status label:

```text
Wide / 80×24                 60-column split
Tests                        Tests
Task       Status  Time      Task       Status  Time
build      PASS    2.1s      build      PASS    2.1s
lint       PASS    0.8s      lint       PASS    0.8s
test       FAIL    4.5s      test       FAIL    4.5s
```

The clutter audit points to four cuts:

- **Border depth: 2 → 0.** Delete the outer frame and inner list border. A heading and whitespace provide enough structure.
- **Duplicate status: 2 → 1.** `[PASS]` and `(ok)` say the same thing. Keep plain `PASS`; remove brackets and `(ok)`.
- **Repeated marker: every row → none.** Remove `>`. If the list is interactive, use reverse video on the selected row only.
- **Row overhead:** `> [PASS] (ok) ` consumes 14 of your example’s 23 cells before the test name. Replace that prefix with aligned columns.

Keep test names prominent, durations right-aligned and visually secondary. Optionally color `FAIL` red; the word must remain readable with `NO_COLOR`.

At 80×24 and 60 columns, retain this single list and scroll vertically. Truncate long names without wrapping; let Enter reveal the full name and failure output. At narrower widths, hide Time first. Set the minimum from the remaining usable content—for example, 30×6—and show a clear “terminal too small” message below it.