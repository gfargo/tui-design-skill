Here's a convention that works well and won't surprise anyone.

## Recommended scheme

| Code | Meaning | Notes |
|---|---|---|
| `0` | Success | |
| `1` | General or unexpected error | Use for anything that doesn't have its own code |
| `2` | Usage error (bad flags, missing args) | Bash builtins, `getopt`, Python's `argparse`, and most Go and Rust CLI libraries all use this |
| `3`–`63` | **Your own codes** | Safe range with no standard meaning |
| `130` | Interrupted by Ctrl-C | Only if you catch SIGINT yourself and exit on purpose (128 + signal 2) |

## Codes to avoid

- **`126` / `127`**: the shell uses these for "found but not executable" and "command not found."
- **`128`+N**: means "killed by signal N." Scripts that check for crashes will misread your codes if you use this range.
- **Above `255`**: the code wraps around (`256` becomes `0`, which looks like success).
- **`64`–`78`**: these come from BSD's `sysexits.h` (`64` usage, `65` bad data, `66` missing input, `69` service unavailable, `70` internal bug, `73` can't create output, `74` I/O error, `75` temporary failure, `77` permission denied, `78` bad config). You can use them, but only with those meanings. Don't reuse them for your own errors.

## Choosing your own codes

- **Start at `3`** and only add a code if a caller would actually branch on it. Examples: `3` = not found, `4` = auth failed, `5` = conflict. If a script would treat two errors the same way, give them the same code.
- **Some tools use non-zero for "no result."** `grep` exits `1` for "no match" and `2` for a real error, and `diff` works the same way. If your CLI answers a yes/no question, consider this pattern.
- **Define the codes once** as named constants or an enum, list them in `--help` or the man page, and never change their numbers after release. Scripts will depend on them.
- **Send errors to stderr**, with a non-zero code. Keep stdout clean for output that other programs read.

If you tell me the language and CLI library you're using, I can sketch the constants and how to wire them in.
