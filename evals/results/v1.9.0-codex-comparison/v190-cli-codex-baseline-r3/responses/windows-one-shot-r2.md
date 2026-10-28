For a **one-shot CLI that must run on Windows**, I’d favor ordinary command output, with a small amount of optional interactivity, over a full-screen TUI.

The main changes:

- **Use a linear flow:** arguments → optional prompts → work → result → exit. Show help or request missing input only when appropriate.
- **Make terminal features optional:** detect whether output is a terminal. Disable animation, cursor movement, and color when redirected; support `--no-color`.
- **Keep automation reliable:** send results to stdout and progress/errors to stderr. Provide stable exit codes and, if useful, `--json`. Never prompt when stdin is redirected.
- **Avoid Unix assumptions:** invoke subprocesses with argument arrays; avoid relying on Bash, `sh`, Unix utilities, executable bits, or POSIX signals.
- **Handle Windows conventions:** use path libraries, account for spaces and backslashes, and test quoting in PowerShell and `cmd.exe`. Avoid hard-coded ANSI sequences and Unicode-dependent layouts.
- **Keep startup and distribution simple:** minimize initialization and provide a Windows-native executable or launcher.
- **Test interruption and cleanup:** Ctrl+C should stop work cleanly and restore any terminal state you changed.

Windows supports rich terminal interfaces, but for a short-lived command, **fast startup, readable output, and predictable scripting behavior** usually matter more than persistent panels or keyboard navigation.