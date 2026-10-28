For a **one-shot CLI, prioritize the stream contract and fast startup**. Windows mainly changes terminal detection, shell assumptions, paths, and cancellation.

- **Stay inline.** Print results to stdout; send errors, prompts, and progress to stderr. Avoid alternate-screen and raw-mode setup.
- **Make automation predictable.** Provide stable `--json` output, documented exit codes, and a non-interactive way to supply every required input. Never hang waiting for a prompt in CI.
- **Detect capabilities per stream.** Animate only when stderr is a terminal. Honor `NO_COLOR` and `--color=auto|always|never`. Windows Terminal may have neither `TERM` nor `COLORTERM`; their absence doesn’t mean “no color.” Use a library that handles Windows virtual-terminal support.
- **Remove Unix shell assumptions.** Don’t depend on `/dev/tty`, `sh`, `less`, or shell-expanded wildcards. Define glob behavior explicitly and support expansion where needed. Pass subprocess arguments as an argument list; document PowerShell quoting.
- **Use platform-aware paths.** Put Windows config under `%APPDATA%\mytool` and cache under `%LOCALAPPDATA%\mytool`. Test paths containing spaces, Unicode, drive letters, and UNC shares.
- **Handle cancellation by platform.** On POSIX, preserve real SIGINT termination after cleanup. Windows uses console events and can report Ctrl+C as `0xC000013A`; don’t blindly translate it to 130. Closed-pipe writes should exit quietly on both platforms.
- **Keep output plain and narrow-friendly.** Border depth: zero. Omit repeated success markers and decorative headers. At 80×24 or 60 columns, wrap help and diagnostics; truncate only human-facing table cells, with a way to reveal full values. Machine output stays complete.

For example, the same command can remain readable at both widths:

```text
Wide:
NAME           STATUS   PATH
report.json    ready    C:\Users\Ann\Documents\report.json

60 columns:
NAME           STATUS   PATH
report.json    ready    C:\Users\Ann\Documents\...
```

**Verify the built CLI on Windows and POSIX**, asserting stdout, stderr, and exact exit codes. Cover redirected streams, `NO_COLOR`, JSON, missing input, Ctrl+C, closed pipes, and Windows path handling. A cross-compile alone won’t verify those behaviors.