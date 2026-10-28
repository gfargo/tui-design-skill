No. Use **`--debug` or a tool-specific variable such as `MYTOOL_DEBUG=1`** to enable stack traces.

Plain `DEBUG` has conflicting conventions: Node’s `debug` package uses namespace patterns, so `DEBUG=*` exported for another tool could unexpectedly flood yours, while `DEBUG=1` matches nothing in that package.

Recommended behavior:

- Default: concise, actionable errors on **stderr**, without stack traces.
- Debug enabled: include stack traces on **stderr**, preserving stdout for results.
- Explicit flags override environment settings.
- Document the flag and environment variable in `--help`.