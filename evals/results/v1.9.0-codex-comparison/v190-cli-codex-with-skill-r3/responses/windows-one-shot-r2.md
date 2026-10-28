Treat it as a **stream-based CLI with a Windows portability layer**. A full-screen TUI framework usually adds little here.

- **Keep output inline:** results on stdout; errors, progress, and prompts on stderr. No alternate screen or raw input mode. Offer stable `--json` output.
- **Make automation predictable:** no prompts without an interactive input channel; document how to supply missing values. Disable animations on redirected stderr. Detect color support independently for each stream, honor `NO_COLOR`, and provide an ASCII fallback.
- **Use small, documented exit codes:** typically `0` success, `1` failure, `2` usage error. Windows has console events rather than POSIX signal semantics: don’t assume SIGPIPE, SIGHUP, suspend/resume, or `128 + signal`. An unhandled Windows Ctrl+C can report `0xC000013A`; don’t blindly rewrite it to `130`. Closed pipes should end quietly.
- **Handle Windows terminals through a library:** enable or verify virtual-terminal processing before emitting ANSI. Missing `TERM` or `COLORTERM` does not mean Windows Terminal lacks color support.
- **Remove Unix shell assumptions:** Windows shells generally leave wildcard expansion to the program. Define glob behavior, use native path APIs, and pass subprocess arguments as an argument list. Include PowerShell examples and completions; don’t require `/dev/tty`, `less`, or Unix utilities.
- **Use platform-specific storage:** `%APPDATA%\mytool` for config and `%LOCALAPPDATA%\mytool` for cache. Verify file-replacement behavior on Windows rather than assuming POSIX rename guarantees.

Keep the presentation borderless and linear. At 80×24, show useful columns; at 60 columns, drop optional columns or switch to labeled records:

```text
Wide                                 60 columns
NAME          STATUS  OUTPUT         report.csv
report.csv    saved   C:\work\...       status: saved
                                       output: C:\work\...
```

Human output may adapt to width; JSON must preserve full values. There’s no need for a “terminal too small” screen.

Test the built executable on Windows and Unix, asserting **stdout, stderr, and exit status**. Cover redirected streams, `NO_COLOR`, Unicode and spaced paths, wildcard arguments, cancellation, and a downstream reader closing its pipe early.