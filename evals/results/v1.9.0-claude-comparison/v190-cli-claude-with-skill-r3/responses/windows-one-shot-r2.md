# One-shot CLI on Windows: what changes

The output contract stays the same: results on stdout, diagnostics on stderr, meaningful exit codes, and plain output when there's no TTY or `NO_COLOR` is set. What changes is the POSIX machinery underneath it: signals, exit-code conventions, ANSI enablement, glob expansion, config paths and atomic renames. Design to the contract and treat each of the items below as a platform branch.

## 1. Signals and exit codes

Windows has no SIGPIPE, no SIGHUP and no 128+N exit codes.

| POSIX habit | On Windows |
|---|---|
| SIGPIPE when `mytool \| head` closes early | Shows up as a plain write error on stdout. **Exit quietly, with no stack trace.** |
| SIGHUP when the terminal closes | Arrives as a console event (`CTRL_CLOSE_EVENT`), not a signal. |
| Re-raise SIGINT so the parent sees death-by-signal | That re-raise (`syscall.Kill`, `emulate_default_handler`, `process.kill(pid,'SIGINT')`) is POSIX-only. Put it behind a platform check. |
| Unhandled Ctrl+C → 130 | The real status is `0xC000013A`. **Don't map it to 130.** |
| Your own exit codes | Keep them small (0–123) so they never collide with signal-style codes on either platform. |

The rest of the Ctrl+C contract carries over: acknowledge right away, bound cleanup with a timeout, and let a second Ctrl+C force-exit. Python's "let `KeyboardInterrupt` propagate" works on both platforms. A program that never installs a handler already behaves correctly.

## 2. Color and ANSI

- **Enable `ENABLE_VIRTUAL_TERMINAL_PROCESSING` before emitting escape codes.** Go (`golang.org/x/sys/windows`), Rust (`anstyle-query`) and Node's tty layer do this for you. Python needs `colorama.just_fix_windows_console()`. The legacy console before the Windows 10 Anniversary Update has no VT processing at all.
- **Don't decide color depth from `TERM` or `COLORTERM`.** Windows Terminal sets neither, so "no `TERM`" doesn't mean "dumb terminal" there. `WT_SESSION` identifies Windows Terminal.
- Decide color separately for each stream (stdout's TTY state for stdout, stderr's for stderr). `NO_COLOR`, `FORCE_COLOR` and `--color` precedence work exactly as on POSIX.
- Unicode output: Go, Rust and Python write through the wide console API, so you don't need `chcp 65001`.

## 3. Arguments and output bytes

- **The shell doesn't expand globs.** `mytool *.log` arrives as the literal string `*.log`, so expand it yourself. Do it only on Windows, or only when no file matches literally, so POSIX shells still own expansion.
- **Emit `\n` only.** Don't switch to CRLF, because golden tests and downstream parsers would differ by platform.

## 4. Config, state and secrets

- **Paths:** `%APPDATA%\mytool` for config, `%LOCALAPPDATA%\mytool` for cache. XDG paths stay the rule on Linux and macOS. Accept `--config PATH` and `MYTOOL_CONFIG` on every platform so users always have an override.
- **Secrets:** use Windows Credential Manager through your keychain library (`zalando/go-keyring`, Rust `keyring`, Python `keyring`). Don't use `keytar` for Node: it's been archived since December 2022.
- **Atomic writes aren't fully guaranteed.** Write a temp file in the same directory, `fsync`, then rename, but replacing an existing file on Windows is only best-effort atomic. Go's `os.Rename` isn't atomic there. In Python use `os.replace`, not `os.rename`. Keep the idempotent, re-runnable design so a torn write can be recovered by running the command again.

## 5. Completions and paging

- **Ship `mytool completion pwsh`** alongside bash, zsh and fish. Cobra, Click (8.5 and later) and Typer generate it. clap needs `clap_complete`. yargs, picocli and commander leave PowerShell to you.
- **Pager:** the reference's rule is to page only when stdout is a TTY, honor `$PAGER`, and never page machine output. My own note, not from the reference: `less` usually isn't installed on Windows, so if no pager is available, write straight to stdout rather than failing.

## 6. Testing

Run the black-box suite (stdout, stderr, exit code, under no-TTY and `NO_COLOR`) on a Windows CI runner too. Add these Windows-specific cases:

- an unmatched literal glob argument;
- early pipe close (`mytool | Select-Object -First 1`) exits quietly;
- an unset `TERM` with stdout as a TTY still gives the right color decision;
- the config path resolves under `%APPDATA%`;
- golden output contains no `\r`.

`testscript`, `trycmd`/`assert_cmd` and Click's `CliRunner` all run on Windows.

## What doesn't apply

A one-shot CLI has no live full-screen UI, so there's no layout to sketch, audit for clutter or test at the 60-column floor. If you add an interactive prompt later, note that Windows also has no SIGTSTP, SIGWINCH or SIGCONT. That means no Ctrl+Z suspend, and resize arrives as console events.

Sources in the skill: `references/cli-basics.md` (sections *Windows*, *Signals*, *Configuration and state*, *Shell completions*, *Testing one-shot CLIs*) and the Windows row of the *Terminal environments* table in `references/terminal-protocols.md`.
