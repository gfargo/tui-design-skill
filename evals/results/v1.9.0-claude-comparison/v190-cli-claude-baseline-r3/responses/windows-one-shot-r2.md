The directory is empty, so this is general guidance rather than a review of your code. By "one-shot CLI" I mean a tool that runs, prints output, and exits, with no full-screen TUI. Here's what changes when it also has to work on Windows.

## Terminal output

- **ANSI escapes:** Windows Terminal and modern PowerShell handle them. Older `conhost` (Win10 cmd.exe) needs VT processing turned on (`ENABLE_VIRTUAL_TERMINAL_PROCESSING`) or it prints raw `←[32m`. Use a library that handles this (chalk/supports-color, colorama/rich, termcolor, crossterm, lipgloss). Don't hand-roll it.
- **Color detection:** Respect `NO_COLOR`, `FORCE_COLOR`, and a `--color=auto|always|never` flag. Check whether stdout is a TTY before writing color. On Windows, `TERM` is usually unset, so don't rely on it.
- **Glyphs:** Emoji, braille spinners and some box-drawing characters show up as `?` or tofu in conhost or with older fonts. Keep an ASCII fallback (`[ok]`, `-\|/`, `+--+`) and use it when the environment can't render the fancy set. `WT_SESSION` being set means Windows Terminal, which renders them fine.
- **Encoding:** The console may be on a legacy code page such as cp437 or cp1252. Python needs `PYTHONUTF8=1` or a reconfigured stdout to avoid `UnicodeEncodeError`. Piped output to a file may also not be UTF-8.
- **Spinners and progress:** `\r` redraws work. Cursor-up and erase-line need VT enabled. Turn animation off entirely when output isn't a TTY, and in CI.
- **Width:** Read it from the terminal API, not `COLUMNS`. There is no SIGWINCH, but a one-shot tool rarely needs it.

## Input, signals and exit

- **Ctrl+C:** It arrives as a console control event, not a real SIGINT, and SIGTERM/SIGHUP mostly don't exist. Put cleanup in `finally` or an exit handler, not just in signal handlers.
- **Exit codes:** Return explicit ones. Don't depend on 128+signal conventions.
- **Prompts:** There is no `/dev/tty`. If stdin is piped, interactive prompts need a fallback or a `--yes` flag.

## Paths and filesystem

- Build paths with the path library, never by joining strings with `/`. Accept both `\` and `/` as input.
- Drive letters, UNC paths (`\\server\share`), case-insensitive names, reserved names (`CON`, `NUL`, `AUX`), and the 260-character path limit unless long paths are enabled.
- Use the platform's config/cache locations (`%APPDATA%`, `%LOCALAPPDATA%`) through platformdirs, env-paths or the `dirs` crate, not `~/.config`.
- Open files may be locked, so deletes and renames can fail with EBUSY/EPERM. Retry, or close handles first.
- Line endings: write `\n` unless the user expects CRLF, and accept CRLF on input. Watch out for git `autocrlf` in test fixtures.

## Arguments and shells

- **Globbing:** cmd and PowerShell don't expand `*.txt`, so your CLI has to glob arguments itself.
- **Quoting:** It differs across cmd, PowerShell and bash, so put copy-pasteable examples for each shell in the docs. PowerShell also treats `--%`, `@` and `$` specially.
- **Env vars:** Names are case-insensitive (`Path` vs `PATH`).

## Spawning other programs

- Executables are found through `PATHEXT` (`.exe`, `.cmd`, `.bat`). `npm`, `npx` and many other tools are `.cmd` shims, which fail with a plain `spawn("npm")`. Use cross-spawn, Python's `shutil.which`, or the `which` crate.
- Avoid `shell: true` and string commands, because argument quoting for `.cmd` files is fragile and a security risk. Pass an argument array.
- Use `where` instead of `which`, and don't assume `sh`, `grep` or `rm` exist.

## Packaging

- Shebangs are ignored. npm generates `.cmd` and `.ps1` shims from `bin`, Python generates `.exe` launchers from `console_scripts`, and Go or Rust produce a `.exe` directly.
- Unsigned binaries can trigger SmartScreen or antivirus warnings. Consider code signing, or distributing through winget or Scoop.

## Testing

- Add `windows-latest` to the CI matrix and run the test suite with stdout both as a TTY and piped.
- Check manually in Windows Terminal, legacy cmd.exe/conhost, and PowerShell 5.1 as well as 7. 5.1 is the one that breaks encoding and quoting.
- Snapshot tests should normalize line endings and path separators.

**Rule of thumb:** Give each output feature a capability check with a plain-text fallback (color, Unicode glyphs, animation, cursor control), and make the fallback what a non-TTY stdout gets. Then Windows mostly behaves like a less capable terminal rather than a separate code path.

If you tell me the language or framework you're using, I can name the specific libraries and settings for it.
