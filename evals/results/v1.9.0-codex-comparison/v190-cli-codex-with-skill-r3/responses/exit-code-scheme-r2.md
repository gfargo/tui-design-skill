Use **0 for success, 1 for general failure, 2 for usage errors**, and assign your own codes starting at 3.

| Code | Meaning |
|---|---|
| `0` | Success, including explicit `--help` and `--version` |
| `1` | Failure without a more specific code |
| `2` | Invalid flags, missing arguments, or invalid argument values |
| `3` | Example: authentication required |
| `4` | Example: requested resource not found |
| `5` | Example: temporary failure; retry allowed |

Choose custom codes only for distinctions scripts need to act on. Document their meanings and which are retryable in `--help`; keep them stable after release.

Keep custom codes within **3–123**. Avoid **124–255**, which overlap with timeout, shell, signal, and `xargs` conventions. On Unix, statuses are only eight bits: `exit(256)` can appear as success.

Write error explanations to **stderr** and results to **stdout**. A cancelled prompt should return `130`; for an actual SIGINT on POSIX, clean up and re-raise the signal so the parent shell recognizes the interruption.