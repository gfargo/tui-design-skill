Use **0 for success**, **2 for usage errors**, and a small set of documented codes for your own failures.

For example:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | General or unexpected failure |
| `2` | Invalid arguments or usage |
| `3` | Requested resource not found |
| `4` | Authentication or permission failure |
| `5` | Operation could not complete |

There’s no universal standard beyond `0` meaning success and nonzero meaning failure. Using `2` for usage errors is a common convention.

Keep your codes in **1–125** for portability. Avoid `126` and `127`, which shells use for command execution failures, and `128+`, commonly used for termination by signals. Avoid negative values or codes above `255`; they may be truncated.

Print diagnostics to **stderr**, and keep exit-code meanings stable so scripts can depend on them.