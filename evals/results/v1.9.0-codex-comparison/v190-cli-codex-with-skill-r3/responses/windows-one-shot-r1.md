**Keep it a conventional CLI: run inline, print results, and exit.** Windows mainly changes platform handling and verification.

- **Preserve the stream contract.** Results go to stdout; errors, prompts, and progress go to stderr. Offer stable `--json` output. Disable animations when stderr isn’t a TTY, and never wait for interactive input in CI.
- **Detect terminal capabilities per stream.** Honor `NO_COLOR` and `--color=auto|always|never`. Use a library that enables Windows virtual-terminal processing before emitting ANSI. Missing `TERM` or `COLORTERM` doesn’t mean Windows Terminal lacks color. Provide ASCII fallbacks.
- **Separate Windows cancellation from POSIX signals.** Windows has no SIGPIPE or SIGHUP. Handle closed-pipe write errors quietly. Handle Ctrl+C through the runtime’s Windows support; don’t translate native unhandled cancellation status `0xC000013A` into Unix exit code 130. Keep application-defined codes small and documented.
- **Remove shell assumptions.** Expand wildcard arguments yourself where promised; Windows shells don’t generally do Unix-style glob expansion for native commands. Use filesystem APIs for paths, pass subprocess arguments as an argument list, and document PowerShell quoting and completions.
- **Use Windows storage locations.** Config belongs under `%APPDATA%\mytool`; cache under `%LOCALAPPDATA%\mytool`. Test replacement of existing files—Unix rename and permission assumptions don’t carry over unchanged.
- **Test on Windows itself.** Assert stdout, stderr, and exit status for success, invalid arguments, redirected input/output, `NO_COLOR`, and closed pipes. Include paths containing spaces and Unicode, plus a real-console Ctrl+C smoke test.

Keep output borderless and linear. At 80 columns, an optional details column can fit; at 60, stack those details:

```text
80 columns                         60 columns
NAME        STATUS   DETAILS       NAME        STATUS
report.csv  written  24 records     report.csv  written
                                     24 records
```

No alternate screen, nested borders, or minimum-height requirement is needed. Human output may adapt to width; machine output must remain complete and stable.