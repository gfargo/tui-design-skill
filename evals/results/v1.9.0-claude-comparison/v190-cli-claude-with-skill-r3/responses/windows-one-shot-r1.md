Your stdout/stderr contract stays the same on Windows. What changes is the plumbing around it: signals and exit codes, turning on ANSI, color detection, globbing, file paths, and atomic writes.

## What stays the same

Results go to stdout and diagnostics to stderr. Exit codes stay meaningful, `--json` output stays stable, `NO_COLOR` is still honored, and you only prompt when there's a TTY. None of this depends on the OS.

## What changes

**1. Signals and exit codes**
- Windows has no SIGPIPE, no SIGHUP and no 128+N exit codes. When the console closes, you get an event (`CTRL_CLOSE_EVENT`), not a signal.
- If you pipe into something that closes early, your write just fails with an ordinary error. Treat that as "the reader went away" and exit quietly. Don't print a stack trace.
- Keep your own exit codes between 0 and 123.
- If Ctrl+C isn't handled, Windows reports status `0xC000013A`. Don't translate that into 130.
- The POSIX advice to "re-raise SIGINT after cleanup" doesn't apply here. Go's `syscall.Kill(getpid, SIGINT)` is POSIX-only, so put it behind a build tag or platform check.

**2. Turn on ANSI before you emit it**
Escape sequences only work after `ENABLE_VIRTUAL_TERMINAL_PROCESSING` is set on the console:
- **Go and Rust** do this for you (`golang.org/x/sys/windows`, `anstyle-query`).
- **Python** needs `colorama.just_fix_windows_console()`.
- **Node**'s tty layer already handles it.

**3. Color detection**
Windows Terminal sets neither `TERM` nor `COLORTERM`. If your logic reads a missing `TERM` as "dumb terminal", every Windows user gets monochrome output. Decide color from whether the stream is a TTY plus `NO_COLOR`/`FORCE_COLOR`. You can use `WT_SESSION` as a sign you're in Windows Terminal.

**4. Arguments and line endings**
- cmd and PowerShell don't expand `*.txt` for you, so your tool gets the literal pattern. Expand globs yourself.
- Write `\n` only, not `\r\n`.

**5. Config, state and secrets**
- Store config in `%APPDATA%\mytool` and cache in `%LOCALAPPDATA%\mytool`. The usual helpers already return these: Go's `os.UserConfigDir`, Rust's `dirs`/`directories`, Python's `platformdirs`.
- For credentials, the keyring libraries (`go-keyring`, Rust and Python `keyring`) use Windows Credential Manager.

**6. Atomic writes**
On Windows, "write a temp file, then rename it over the target" is only best effort. Go's `os.Rename` isn't atomic there. In Python, use `os.replace`, not `os.rename`. Your rule against leaving a truncated file at the final path still applies.

**7. Unicode and symbols**
- Go, Rust and Python write through the wide console API, so you don't need `chcp 65001`.
- The old conhost console still has unreliable glyphs. Keep an ASCII fallback for ✓/✗-style markers, and make sure the text says the outcome on its own, without relying on color.

**8. Optional terminal extras**
- Hyperlinks (OSC 8) work in Windows Terminal 1.4+. Strip them when stdout isn't a TTY, as you would anywhere.
- Taskbar progress (OSC 9;4) works in Windows Terminal. Clear it (state 0) on every exit path.
- Target Windows Terminal, which has been the default since Windows 11 22H2. Pre-Anniversary-Update Windows 10 consoles have no VT support at all.

## Testing

Run your existing black-box golden tests on a Windows CI runner too. Keep checking stdout, stderr and the exact exit code, with no TTY and with `NO_COLOR`. Add Windows-specific cases for:
- a glob argument (`mytool *.txt`) that's expanded correctly;
- writing into a closed pipe (exits quietly with a small code);
- no `\r\n` in golden output;
- config landing under `%APPDATA%`.

Tools that work: Go's `testscript` (add a custom command to check exact exit codes), Rust's `trycmd`/`assert_cmd`, and Click/Typer's `CliRunner`.

These details come from the skill's `references/cli-basics.md` and `references/terminal-protocols.md`. If you tell me your language, I can turn this into the exact code for your stack.
