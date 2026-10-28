No—use `--debug` and a tool-specific variable such as `MYTOOL_DEBUG=1`.

Plain `DEBUG` is widely used by Node’s `debug` package for namespace matching. A user’s `DEBUG=*` intended for another tool could unexpectedly enable your stack traces; `DEBUG=1` has different semantics there.

Recommended behavior:

- Default: concise errors explaining what failed and how to fix it.
- Debug enabled: include stack traces on **stderr**, keeping stdout clean for results.
- Let explicit CLI flags override environment settings, and document accepted values.

```sh
mytool --debug fetch
MYTOOL_DEBUG=1 mytool fetch
```