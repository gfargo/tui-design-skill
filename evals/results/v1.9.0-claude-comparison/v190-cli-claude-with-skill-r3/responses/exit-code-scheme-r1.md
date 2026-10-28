Use **0** for success, **1** for a general failure, **2** for usage errors, and put your own codes in **3–123**.

## Recommended scheme

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | General failure: anything without a more specific code |
| `2` | Usage error: unknown flag, missing argument, invalid value |
| `3–123` | Your own codes. Document every one |
| `124–128` | Don't use. `timeout` uses 124 and 125. The shell uses 126 (not executable), 127 (command not found) and 128 |
| `129–255` | Don't use. 128 + N means "killed by signal N" (130 is Ctrl-C/SIGINT, 137 is SIGKILL, 143 is SIGTERM), and 255 makes `xargs` stop |

Exit 2 for usage errors isn't a formal standard, but bash builtins, Python's argparse, Rust's clap and Go's `flag` all use it. If you use one of those parsers, you probably get 2 already.

## Your own codes

Number them from 3 upward, one per failure class that a script would handle differently. For example:

```
0  ok
1  error (unspecified)
2  usage error
3  config error (bad or missing config file)
4  not found (the resource/file the user named doesn't exist)
5  permission denied
6  network/service unavailable — safe to retry
```

Guidelines:
- **Only add a code if a caller would branch on it.** If no script would treat a failure differently from any other, use 1.
- **Mark which codes are safe to retry.** That's usually what callers most need to know.
- **List the codes in `--help`** and keep them stable. Changing a code number breaks scripts.
- **Keep codes at 255 or below.** The status is 8 bits, so `exit(256)` is read as `0`, which means success. If you compute a code, clamp it.
- **"No results" can be its own code** if scripts need it. `grep` and `rg` use `0` for match found, `1` for no match and `2` for error. Only do this if it's useful, and document it.

## Edge cases

- **Cancelled prompt** (the user presses Ctrl-C or Esc at an interactive question): restore the terminal and exit **130**, not 0. Otherwise `mytool init && mytool deploy` would go ahead without an answer.
- **Real SIGINT during work:** don't call `exit(130)`. Clean up, then re-raise the signal so the parent shell sees the process died from SIGINT. Bash stops a loop or script only when the child died from the signal. For example, in Python, let `KeyboardInterrupt` propagate instead of calling `sys.exit(130)`.
- **SIGPIPE** (e.g. `mytool | head`): exit quietly with 0 or 141, with no stack trace.
- **Partial results:** if any part of the work didn't finish, exit non-zero.
- **`--json` errors:** use the same non-zero code as the human-readable error. Write one JSON line to stderr with a stable `code` string (like `"permission_denied"`) and leave stdout empty.
- **Windows:** there are no signal codes. Keep your codes in 0–123 and don't turn an unhandled Ctrl+C into 130.

## The sysexits.h alternative

BSD's `sysexits.h` defines codes 64–78: 64 for usage, 65 for bad data, 66 for no input, 69 for unavailable, 70 for an internal error, 75 for a temporary (retryable) failure, 77 for permission and 78 for config. These codes don't clash with the ranges above. They're an older convention that isn't portable, so either use the whole set or none of it. Mixing them with 1 and 2 is confusing. For a new tool, the small numbered scheme above is simpler.

## Testing

Test the built binary from the outside, checking **stdout, stderr and the exit code** together. Include runs with no TTY and with `NO_COLOR` set, plus at least one case per exit code you define.

If you tell me the language or argument parser you're using, I can show how to wire these codes in so usage errors get 2 automatically.
