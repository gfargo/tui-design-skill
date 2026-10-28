The working directory is empty, so this is general advice. If you tell me your language or framework, I can make it specific.

The good news is that a one-shot CLI (runs, prints, exits) avoids the hardest Windows terminal problems: full-screen mode, raw input and resize events. What's left is mostly about output, paths and the shell.

## Terminal output
- **ANSI/VT sequences:** Windows Terminal and PowerShell 7 handle them. Older conhost windows need `ENABLE_VIRTUAL_TERMINAL_PROCESSING` turned on. Use a library that does this for you (colorama/rich, chalk/supports-color, crossterm, termcolor) rather than writing raw escape codes.
- **Color detection:** Check whether output is a TTY. Respect `NO_COLOR` and `--no-color`. When output is piped, drop color and animation entirely.
- **Palette:** Windows PowerShell 5.1 has a dark blue background by default, so dark blue and magenta text become unreadable. Stick to bright or bold colors, and don't rely on dim, italic or underline.
- **Glyphs and encoding:** Legacy consoles use code pages like cp437 or cp1252, so `✔ ✖ ⠋` and emoji can come out as garbage or `?`. Force UTF-8 output (e.g. `sys.stdout.reconfigure(encoding="utf-8")`) and keep ASCII fallbacks for spinners and status marks.
- **Spinners and progress bars:** Redrawing with `\r` works fine. Always restore the cursor on exit, including on Ctrl+C. Windows has no `SIGWINCH` or `SIGTERM` in the POSIX sense. Ctrl+C arrives through a console control handler, which most runtimes map to SIGINT/KeyboardInterrupt.
- **Width:** Get it from your runtime's terminal-size API, not `tput` or `$COLUMNS`.

## Paths and filesystem
- Build paths with path libraries. Never hardcode `/`, `/tmp` or `~/.config`. Use `%APPDATA%` / `%LOCALAPPDATA%` (or `platformdirs`/`env-paths`) and the OS temp dir.
- Display paths in native form (`C:\Users\...`) in messages.
- Plan for drive letters, case-insensitive matching, reserved names (`CON`, `NUL`, `AUX`), the 260-character `MAX_PATH` limit, and files locked by another process (deleting or renaming an open file fails).
- **Line endings:** Expect CRLF in input files. Choose line endings deliberately when writing files, because text-mode stdout may translate `\n` to `\r\n`.

## Shell and arguments
- **No glob expansion:** cmd and PowerShell don't expand `*.txt`, so your CLI has to do it.
- **Quoting:** Rules differ between cmd and PowerShell. Help text examples should work in both, or show both versions. Single quotes don't work in cmd.
- **Redirection encoding:** In Windows PowerShell 5.1, `>` writes UTF-16. Users who save your output to a file may get unexpected encoding, so a `--output FILE` flag is worth having.
- **Subprocesses:** There are no shebangs, and tools like `npm` are `.cmd` shims. Resolve executables through `PATHEXT` (`shutil.which`, `cross-spawn`) instead of assuming a bare name runs.

## Exit and errors
- Keep exit codes between 0 and 255. Ctrl+C on Windows shows up as `0xC000013A`, not 130, so map it yourself if scripts depend on it.
- Send errors to stderr so piping still works.

## Prompts
- If the CLI ever asks questions, put a flag behind every one (`--yes`, `--name=`). Fall back to non-interactive mode when stdin isn't a TTY. Arrow-key menus are the least reliable thing across Windows consoles.

## Distribution and testing
- Unsigned `.exe` files trigger SmartScreen and antivirus warnings. Plan for code signing or ship through a package manager (winget, scoop, npm, pipx).
- Add `windows-latest` to your CI matrix. Do one manual pass in **conhost + Windows PowerShell 5.1** (the worst case) and one in **Windows Terminal + PowerShell 7** (the common case).

**Short version:** detect capabilities instead of assuming them, keep ASCII and no-color fallbacks, let libraries handle paths and processes, and test in old conhost at least once.
