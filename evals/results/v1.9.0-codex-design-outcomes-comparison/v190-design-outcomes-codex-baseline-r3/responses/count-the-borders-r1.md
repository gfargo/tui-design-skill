Remove these elements:

- **Both layers of boxes around each pane.** Keep only the outer screen border.
- **Every `>`**. Reserve it for the selected row: `api`.
- **`ok`, `fail`, `v`, and `x`.** They repeat PASS/FAIL, which already has color.
- **`job: api` and `status: PASSED (v)` in the detail pane.** They repeat the selected row. Keep duration.

The busyness comes from nested borders and repeated status signals competing with three rows of information.

Afterward, with PASS still green and FAIL still red:

```text
+----------------------------------------------------------------------+
| BUILD MONITOR                                                        |
|                                                                      |
| > api       PASS                      Duration: 2m 10s               |
|   web       PASS                                                     |
|   worker    FAIL                                                     |
|                                                                      |
+----------------------------------------------------------------------+
```