A practical convention is:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | General or unexpected failure |
| `2` | Usage error: invalid arguments, missing required flags |
| `3`–`125` | Your documented, application-specific errors |

For example, you could use `3` for missing configuration, `4` for authentication failure, and `5` for a failed remote request.

Avoid assigning these yourself:

- `126`: command found but cannot execute
- `127`: command not found
- `128` and above: commonly used for signal-related exits, such as `130` for Ctrl-C

There’s also the Unix `sysexits.h` convention, where usage errors are `64`. Use that if your ecosystem expects it; otherwise, **`2` for usage errors is a sensible default**.

Print error messages to **stderr**, and keep your documented codes stable so scripts can rely on them.