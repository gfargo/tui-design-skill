## Recommended exit codes

**Use the common conventions:**

| Code | Meaning | Notes |
|---|---|---|
| `0` | Success | |
| `1` | General or runtime error | The catch-all for failures |
| `2` | Usage error (bad flags or args) | Bash builtins, `getopt`, Python's `argparse` and most CLIs use this |

**Reserved codes to avoid:**

| Code | Meaning |
|---|---|
| `126` | Command found but not executable (set by the shell) |
| `127` | Command not found (set by the shell) |
| `128+N` | Killed by signal N, e.g. `130` = Ctrl-C (SIGINT), `143` = SIGTERM |
| `>255` | Wraps modulo 256, so `256` becomes `0`. Never use these. |

**`sysexits.h` (64–78):** BSD defines `EX_USAGE=64`, `EX_DATAERR=65`, `EX_NOINPUT=66`, `EX_UNAVAILABLE=69`, `EX_SOFTWARE=70`, `EX_CANTCREAT=73`, `EX_IOERR=74`, `EX_TEMPFAIL=75`, `EX_NOPERM=77`, `EX_CONFIG=78`, and a few others. Some tools use these, mainly mail and daemon tools. If one of them matches your case exactly, reuse it. Don't invent your own meanings for numbers in this range.

## Where to put your own codes

Use **3–63**. That range avoids the shell's reserved codes, signal codes and sysexits. For example:

```
0   OK
1   general error
2   usage error
3   config file missing or invalid
4   network/remote unavailable
5   auth failure
6   partial success (some items failed)
```

## Tips

- **Usage errors:** print a short message plus a hint like "see `--help`" to stderr, then exit `2`. `--help` itself should exit `0`.
- **Ctrl-C:** if you catch SIGINT, exit with `130` so that shells and scripts can tell the run was interrupted.
- **"No results":** this doesn't always need to be an error. `grep` uses `1` for "no match" and `2` for a real error. If scripts will branch on "empty vs. failed", copy that pattern.
- **Documentation:** list the codes in `--help` or the man page under an `EXIT STATUS` section. Define them once as named constants (an enum or consts) so they stay stable. Once scripts depend on these numbers, changing one breaks them.

If you tell me the language you're writing in, I can sketch the constants and the top-level error handler.
