Generally, **use `--debug` or a namespaced variable like `MYCLI_DEBUG=1`**, rather than the generic `DEBUG`.

`DEBUG` is often set for other tools and libraries, so honoring it could unexpectedly expose stack traces or turn on unrelated logging.

A good default:

- Show concise, actionable errors normally.
- Include stack traces when `--debug` or `MYCLI_DEBUG=1` is enabled.
- Write diagnostics to stderr so stdout stays usable in scripts.
- Keep credentials and other secrets out of diagnostics.

If your ecosystem already defines a `DEBUG` convention, follow its matching rules—for example, `DEBUG=mycli:*`—instead of treating any nonempty value as enabled.