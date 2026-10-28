Generally, use a namespaced variable such as `MYCLI_DEBUG=1` and an explicit `--debug` flag. `DEBUG` is widely used by libraries and may already be set for unrelated reasons, causing your CLI to expose stack traces unexpectedly.

A good default:

- Normal mode: concise error message and actionable guidance.
- Debug mode: full stack trace and diagnostic details, written to stderr.
- Treat unset, empty, `0`, and `false` as disabled; document accepted values.

If your ecosystem already gives `DEBUG` a specific meaning, follow that convention—but avoid treating any nonempty value as a request for stack traces.