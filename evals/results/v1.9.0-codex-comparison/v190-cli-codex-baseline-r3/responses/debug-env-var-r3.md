Usually, **use `--debug` or a namespaced variable like `MYCLI_DEBUG=1` for stack traces**, rather than the generic `DEBUG` variable.

`DEBUG` is already used by many libraries—often with namespace patterns such as `DEBUG=mycli:*`. Reading any nonempty value as “show stack traces” can unexpectedly enable them when users are debugging something else.

A useful convention:

- **Default:** concise error message with actionable context.
- **`--debug` / `MYCLI_DEBUG=1`:** include stack traces and diagnostic details.
- **Unexpected internal errors:** suggest rerunning with `--debug`.

If your ecosystem already defines a `DEBUG` convention, follow its matching rules. Keep credentials and other secrets out of diagnostic output.