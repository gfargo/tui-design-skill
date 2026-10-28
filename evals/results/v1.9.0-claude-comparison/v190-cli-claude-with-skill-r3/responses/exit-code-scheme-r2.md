Use **2 for usage errors**, and put your own codes in **3–123**, numbered from 3 upward. Don't use anything from 124 up. Those values belong to the shell, `timeout`, and signal deaths.

## Recommended scheme

| Code | Meaning | Who owns it |
|---|---|---|
| **0** | Success | You |
| **1** | General failure, when nothing more specific fits | You |
| **2** | Usage error: unknown flag, bad or missing argument | You. bash builtins, argparse, clap and Go's `flag` all use 2 |
| **3–123** | Your own failure classes, each one documented | You |
| 124–125 | `timeout` and its own errors | Not yours |
| 126 / 127 | Not executable / command not found | The shell |
| 128+N | Killed by signal N: 130 = Ctrl‑C, 137 = SIGKILL, 143 = SIGTERM | Not yours |
| 255 | Makes `xargs` stop | Not yours |

A set of custom codes might look like this (the names are only examples):

```
0  ok
1  error (unspecified)
2  usage error
3  config error        (bad or missing config file)
4  not found           (the target resource doesn't exist)
5  auth failed
6  temporary failure   (network, rate limit; safe to retry)
```

## Rules that matter

- **Clamp computed codes.** The exit status is only 8 bits, so `exit(256)` shows up as **0**, which is success. Never pass a count or an errno through as the exit code without clamping it.
- **Say which codes are retryable.** Scripts need to know which failures they can retry. In the example above, only 6 is retryable, and that should be stated.
- **List the codes in `--help`.** Add a short "Exit status" section.
- **A cancelled prompt is not success.** If the user presses Ctrl‑C or Esc at an interactive prompt, restore the terminal and exit **130**. Exiting 0 would let `mytool init && mytool deploy` continue without an answer.
- **For a real SIGINT, re-raise the signal; don't call `exit(130)`.** Clean up, restore the default handler, and send SIGINT to yourself. bash only stops a script or loop when the child actually died from SIGINT. A child that exits 130 looks like it handled the signal, so the loop keeps going. In Python, let `KeyboardInterrupt` propagate.
- **SIGPIPE** (for example, when piping into `head`): exit quietly with 0 or 141, and never print a stack trace.
- **Partial results** should exit non-zero.
- **`--json` errors** should exit with the same non-zero code as the human-readable error. Put a stable string `code` field in the JSON on stderr so scripts can branch on it without relying on the number alone.
- **Windows** has no 128+N codes. Keep your codes in 0–123 and they work the same on every platform.

## What about `sysexits.h`?

BSD's `sysexits.h` defines codes like 64 = `EX_USAGE`, 75 = `EX_TEMPFAIL` and 78 = `EX_CONFIG`. These fall inside the 3–123 range, so they're allowed. Still, they're a legacy, non-portable vocabulary, and most modern CLIs (`gh`, `rg`, cargo) use a small custom set like the one above. If you do adopt sysexits, use all of it: 64 for usage instead of 2, and 75 as your retryable code. Don't mix it with a custom scheme.

One more option: if your tool works like a search or check command, you can follow `grep`/`rg` and use 0 = found, 1 = not found, 2 = error. That only makes sense if "nothing matched" is a normal result and not a failure.

Finally, test the exit code along with stdout and stderr in your black-box tests, with no TTY attached, so a change to the codes shows up as a failing test.
