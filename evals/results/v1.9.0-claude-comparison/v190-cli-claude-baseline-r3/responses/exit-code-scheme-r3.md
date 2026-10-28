Here's a scheme that matches what shells and other tools already expect.

## The standard ones

| Code | Meaning | Notes |
|---|---|---|
| `0` | Success | |
| `1` | General or unspecified error | The catch-all |
| `2` | Usage error (bad flags or arguments) | Bash builtins, `grep`, `ls`, argparse, and most CLI libraries use this |

For usage errors, **use `2`**. It's the most common convention.

## Ranges to avoid

- **126**: command found but not executable (the shell sets this)
- **127**: command not found (the shell sets this)
- **128+N**: killed by signal N, e.g. `130` for Ctrl-C (SIGINT) and `143` for SIGTERM. If you catch SIGINT and exit cleanly, exiting with `130` is good practice.
- **Above 255**: exit codes are taken mod 256, so `256` becomes `0`, which is wrong.

## Where your own codes go

**Option A: small custom codes (3–63).** This is the simplest choice and works well for app-specific failures:

```
0  success
1  general error
2  usage error
3  config error (missing/invalid config file)
4  network/remote failure
5  auth failure
6  not found (requested resource doesn't exist)
```

**Option B: BSD `sysexits.h` (64–78).** This is an older standard, still used by mail tools and some Unix utilities:

```
64 EX_USAGE        bad command-line usage
65 EX_DATAERR      bad input data
66 EX_NOINPUT      input file missing/unreadable
69 EX_UNAVAILABLE  service unavailable
70 EX_SOFTWARE     internal bug
73 EX_CANTCREAT    can't create output file
74 EX_IOERR        I/O error
75 EX_TEMPFAIL     temporary failure, retry later
77 EX_NOPERM       permission denied
78 EX_CONFIG       configuration error
```

My recommendation is to use **0 / 1 / 2** and put your own codes in **3–63**. If one of your errors matches a sysexits meaning, you can borrow that number, especially `75` (temporary failure, retry), which scripts can act on.

## Tips

- Only give an error its own code if a script would branch on it, like retrying on a network failure. Everything else can be `1` with a clear message on stderr.
- Define the codes as named constants in one place and list them in `--help` or the man page. Once people script against them, they're a public API.
- Some tools give a non-error result its own code, like `grep` returning `1` for "no matches" versus `2` for "error", or `diff` returning `1` for "files differ". If your CLI answers a yes/no question, consider doing the same.
