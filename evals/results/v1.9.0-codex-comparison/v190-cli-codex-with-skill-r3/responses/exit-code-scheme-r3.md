Use **0 for success, 1 for general failure, 2 for usage errors, and 3–123 for your own documented codes**.

A practical starting point:

| Code | Meaning |
|---|---|
| `0` | Success, including explicit `--help` and `--version` |
| `1` | General or unexpected failure |
| `2` | Invalid flags, missing arguments, or invalid argument values |
| `3` | Configuration error |
| `4` | Authentication or permission failure |
| `5` | Temporary failure; retry may succeed |

Codes `3–5` are your choices, not universal conventions. Add distinctions only when scripts can act on them.

Avoid assigning custom codes **124–255**: timeout tools, shells, and signal reporting use that range. On POSIX, statuses are limited to 8 bits—`exit(256)` can appear as success.

Document the meanings in `--help`, keep them stable, and send error explanations to **stderr**. For a new CLI, this small scheme is usually preferable to adopting the legacy BSD `sysexits.h` codes.