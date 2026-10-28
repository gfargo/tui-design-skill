Short version: the stream contract stays the same: results on stdout, diagnostics on stderr, meaningful exit codes. What changes is everything that assumes POSIX underneath: signals, exit-code conventions, how ANSI and color get turned on, globbing, line endings, paths, and file replacement. Most of this comes from the skill's `references/cli-basics.md` → *Windows*, with environment notes from `references/terminal-protocols.md` → *Terminal environments*.

## What changes

**1. Signals and exit codes**
- Windows has no SIGPIPE, no SIGHUP and no "128 + signal number" exit codes. Closing the console window arrives as a `CTRL_CLOSE_EVENT`, not a signal.
- When the consumer closes the pipe early (`mytool | Select-Object -First 5`), your write just fails with an ordinary error. Treat that as a quiet exit, with no stack trace, the same way you'd treat EPIPE on Unix.
- Keep your own exit codes in the 0–123 range. Don't translate an unhandled Ctrl+C (status `0xC000013A`) into 130; 130 is a POSIX convention.
- The Unix advice to re-raise SIGINT after cleanup uses POSIX-only calls (for example Go's `syscall.Kill`). Put that path behind a build tag or platform check.

**2. Turning on ANSI color**
- The console has to have `ENABLE_VIRTUAL_TERMINAL_PROCESSING` enabled before you write escape codes:
  - **Go and Rust:** handled for you (`golang.org/x/sys/windows`, `anstyle-query`).
  - **Python:** call `colorama.just_fix_windows_console()` at startup.
  - **Node:** its tty layer already does it.
- Windows Terminal sets neither `TERM` nor `COLORTERM`. If your color detection reads those, it will wrongly decide there's no color. Use `WT_SESSION` to recognise Windows Terminal and isatty to decide whether to style at all.
- `NO_COLOR` and the pipe check work exactly as on Unix.

**3. Globs, newlines and text**
- The shell doesn't expand globs. `mytool *.log` passes the literal string `*.log` to your program, so expand patterns yourself.
- Write `\n` only, never `\r\n`.
- For Unicode output, Go, Rust and Python write through the wide console API, so you don't need `chcp 65001`. Target Windows Terminal, which has been the default since Windows 11 22H2. Older conhost has no VT support before the Windows 10 Anniversary Update.
- If you draw box characters or spinners, have an ASCII fallback and an `--ascii` override (`visual-patterns.md` → *ASCII fallback*). Note that the reference detects UTF-8 from `LC_ALL`, `LC_CTYPE` and `LANG`, and those usually aren't set on Windows. So on Windows, rely on the explicit flag rather than locale sniffing. (That last point is my inference, not something the reference says.)

**4. Files, config and secrets**
- **Config locations:** config goes in `%APPDATA%\mytool` and cache in `%LOCALAPPDATA%\mytool`. Go's `os.UserConfigDir`, Rust's `dirs` and `platformdirs` give you these.
- **Atomic writes:** write-temp-then-rename is best effort on Windows, not guaranteed atomic. Go's `os.Rename` isn't atomic there. In Python use `os.replace`, not `os.rename`. Still write the temp file in the same directory, and never leave a truncated file at the final path.
- **Secrets:** keep them out of flags. Windows Credential Manager is the keychain backend (`go-keyring`, Rust `keyring`, Python `keyring`).

**5. Completions and paging**
- Add `pwsh` to `mytool completion <bash|zsh|fish|pwsh>`:
  - **Built in:** Cobra, Click 8.5+ and Typer generate PowerShell completions.
  - **Not built in:** yargs, picocli and commander don't. clap needs `clap_complete` and oclif needs `@oclif/plugin-autocomplete`.
- Only page when stdout is a TTY, and honor `$PAGER`. Don't assume `less` exists on a stock Windows machine; if neither `$PAGER` nor a pager is available, print directly. (The `less` point is my inference, not from the reference.)

**6. Interactive prompts**
- Gate prompts on isatty for both stdin and stdout, and keep the environment-variable bypass for non-interactive use (as `GH_TOKEN` does).
- If you write prompt UI to `/dev/tty` on Unix, that path doesn't exist on Windows. Use the framework's console handling, or write the prompt to stderr. (Also my inference.)

## Testing
- Run the black-box golden tests (stdout, stderr and exit code, with no TTY and under `NO_COLOR`) on a Windows CI runner too: `testscript` for Go, `trycmd`/`assert_cmd` for Rust, `CliRunner` for Click/Typer.
- Add Windows-specific cases:
  - a literal `*.txt` argument gets expanded;
  - a closed pipe exits quietly with your normal code;
  - output contains no `\r\n`;
  - the exit code is in range after an error.

## What doesn't change
- `--json` stability.
- The `error:` message format.
- The flag vocabulary.
- `--dry-run` and idempotency.
- Startup-time budget.

There's no layout to sketch for a one-shot CLI. The 60-column check only matters if you print tables, and then the rule is to truncate rather than wrap.

If you tell me the language, I can turn this into the concrete startup code (VT enable, pipe-error handling, glob expansion) and a Windows CI test matrix.
