Use **0 for success, 1 for general failure, 2 for usage errors**, then assign a few documented codes starting at 3.

| Code | Meaning |
|---|---|
| `0` | Success, including explicit `--help` and `--version` |
| `1` | Failure without a more specific code |
| `2` | Invalid usage: unknown flag, missing argument, invalid argument value |
| `3` | Example: configuration error |
| `4` | Example: authentication or permission failure |
| `5` | Example: temporary failure callers may retry |

Choose custom codes only for distinctions scripts need to act on. Keep their meanings consistent across subcommands and document them in `--help`.

Keep custom codes within **3–123**. Avoid **124–255**, which overlap timeout, shell, and signal conventions; `255` also makes `xargs` stop. On POSIX, exit statuses are only eight bits—`exit(256)` becomes `0`.

Write errors to **stderr**, results to **stdout**, and keep shipped codes stable. You don’t need BSD `sysexits.h` unless you’re matching an existing contract.