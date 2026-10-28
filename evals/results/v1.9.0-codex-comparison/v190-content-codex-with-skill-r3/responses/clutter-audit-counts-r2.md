Remove both boxes and give each row one status label:

```text
Wide / 80×24                 60-column split
Task     Status   Time       Task     Status   Time
build    PASS     2.1s       build    PASS     2.1s
lint     PASS     0.8s       lint     PASS     0.8s
test     FAIL     4.5s       test     FAIL     4.5s
```

Using the tui-design clutter audit:

- **Border depth: 2 → 0.** Remove the outer frame and inner list border; a heading and whitespace provide enough structure.
- **Duplicate status: 2 → 1.** `[PASS]` and `(ok)` say the same thing. Keep `PASS`, drop its brackets and `(ok)`.
- **Repeated marker: every row → none.** Remove `>`. If the list is interactive, show the selected row with reverse video alone.
- **Row overhead:** `> [PASS] (ok) ` consumes 14 of your example’s 24 characters before the task name even starts.

Keep names left-aligned and durations right-aligned. Leave passes in the default foreground; optionally color `FAIL` red while retaining the word so monochrome stays clear.

At 80×24 and 60 columns, keep this single list and scroll vertically. Truncate long names rather than wrapping; let Enter reveal the full name and output. Below the width needed for name plus status, hide durations first. Show “terminal too small” only when those essential fields and controls no longer fit.