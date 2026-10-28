No—use `--debug` and a tool-specific variable such as `MYTOOL_DEBUG=1`.

Plain `DEBUG` is widely used by Node’s `debug` package for namespace filtering. An inherited `DEBUG=*` could unexpectedly enable your traces, while `DEBUG=1` matches nothing under that package’s semantics.

For your CLI:

- Default to concise, actionable errors without stack traces.
- Enable traces explicitly with `--debug` or `MYTOOL_DEBUG=1`.
- Write diagnostics to **stderr**, keeping stdout reserved for results.
- Document accepted environment values and let explicit flags override them.