Use **0** for success, **1** for a general failure, **2** for usage errors, and put your own codes in **3–123**. Don't use anything at 124 or above.

## Recommended scheme

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Failure with no more specific code |
| 2 | Usage error: bad flag, missing argument, unknown subcommand |
| 3–123 | Your own documented codes |
| 124–128 | Reserved. `timeout` uses 124 and 125. The shell uses 126 (not executable), 127 (command not found) and 128 |
| 129–255 | Reserved. 128 + N means "killed by signal N": 130 is Ctrl-C, 137 is SIGKILL, 143 is SIGTERM. 255 also makes `xargs` stop early |

**Why 2 for usage errors:** it isn't a universal rule, but bash builtins, Python's argparse, Rust's clap and Go's `flag` all use it. Users and scripts already expect it.

## Your own codes

Give each failure that a script might handle differently its own number. For example:

```
3  not found (the requested resource doesn't exist)
4  permission denied / auth failure
5  conflict (already exists, stale version)
6  temporary failure, so it's safe to retry
7  config error
```

Rules for these:
- **Only add a code if a caller would act on it.** If no script would branch on the difference, use 1.
- **State which codes are safe to retry.** Callers need this most.
- **Clamp any code you compute.** The exit status is 8 bits, so `exit(256)` becomes 0 and reports success.
- **List the codes in `--help`** and never change an existing number's meaning. They're part of your public interface.
- **Match codes in `--json` mode.** If you write a JSON error to stderr, use the same exit code as the plain-text error and include a stable string `code` field (e.g. `"permission_denied"`) that scripts can match on.

**About sysexits.h:** BSD's `sysexits.h` defines codes 64–78 (64 for usage errors, 75 for temporary failures, 78 for config errors, and so on). They fall inside the 3–123 range, so you can use them. Either use the whole set or none of it, though. Don't put 64 for usage errors next to your own 3–7. It's an older Unix convention, and most modern CLIs use a short scheme like the one above.

## Edge cases

- **Cancelled prompt → exit 130, not 0.** If the user cancels an interactive prompt, restore the terminal and exit 130. Exiting 0 would let `mytool init && mytool deploy` keep going without an answer.
- **Real Ctrl-C → re-raise the signal; don't call `exit(130)` yourself.** Clean up, restore the default handler, then send SIGINT to your own process. Bash only stops a script or loop if the child process actually died from the signal. A process that catches Ctrl-C and exits 130 looks to bash like it handled the interrupt, so the loop carries on. In Python, let `KeyboardInterrupt` propagate instead of calling `sys.exit(130)`.
- **Broken pipe (`mytool | head`) → exit quietly with 0 or 141.** Never print a stack trace.
- **Truncating on request → exit 0.** If `--limit` cut off results, print a note on stderr saying how to get the rest. Doing what was asked isn't an error.
- **Partial or incomplete results → non-zero.** Don't leave a half-written file at the final path.
- **On Windows, keep your codes small.** Windows has no signal-based codes, so stay within 0–123.

## Test them

Golden tests should run the built binary and check stdout, stderr and the exit code together, with no TTY and with `NO_COLOR` set. For example:

```python
assert (r.exit_code, r.stdout, r.stderr) == (2, "", "error: unknown flag --frobnicate\n")
```
