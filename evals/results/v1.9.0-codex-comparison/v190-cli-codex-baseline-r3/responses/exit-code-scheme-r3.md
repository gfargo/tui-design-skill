A simple, predictable scheme is:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | General or unexpected failure |
| `2` | Usage error: invalid flags, missing arguments, invalid combinations |
| `3` | Your first specific failure, such as configuration error |
| `4` | Another specific failure, such as authentication failure |
| `5` | Another specific failure, such as resource not found |

For your custom codes, choose a few stable values in `3–63` and document them so scripts can rely on them.

Avoid `126` and `127` (shell execution errors), and `128+` (commonly used for signal termination, such as `130` for Ctrl-C). Keep codes within `0–255`.

There’s also the Unix `sysexits.h` convention, which uses `64` for usage errors, but **`2` is a common, sensible choice for a general-purpose CLI**. Print error details to stderr; use exit codes for broad failure categories.