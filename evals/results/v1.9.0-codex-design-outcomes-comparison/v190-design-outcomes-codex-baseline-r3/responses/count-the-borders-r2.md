Remove these elements:

- **Both inner boxes.** Nested borders consume space without adding structure.
- **All `>` markers.** Reserve one for the selected job.
- **`ok`, `fail`, `v`, and `x`.** They repeat PASS/FAIL.
- **The brackets around status labels.** Color and column alignment already distinguish them.
- **`job: api` and `status: PASSED (v)` in the detail pane.** They repeat the selected row. Keep duration beside its job and remove the pane entirely.

Keep PASS green and FAIL red, with the words intact so color isn’t the only signal. At 72 columns:

```text
+----------------------------------------------------------------------+
| BUILD MONITOR                                                        |
|                                                                      |
|   JOB          STATUS     DURATION                                   |
| > api          PASS       2m 10s                                      |
|   web          PASS                                                  |
|   worker       FAIL                                                  |
|                                                                      |
+----------------------------------------------------------------------+
```

The original gives each result four signals—word, brackets, extra word, symbol—then repeats the selected result inside two more borders. One status per row makes the failure easier to find.