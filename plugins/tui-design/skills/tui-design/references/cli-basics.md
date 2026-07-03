# Simple CLI design — non-TUI command-line tools

For programs that don't have a full-screen UI: read args, do work, print output, exit. This document synthesizes [clig.dev](https://clig.dev), the [12-Factor CLI](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46) principles, POSIX.1-2017 utility conventions, GNU coding standards, the XDG Base Directory Specification, BSD `sysexits.h`, and the design of widely admired CLIs (`gh`, `rg`, `fd`, `bat`, `jq`, `httpie`, `kubectl`, `docker`, `starship`).

The bar for a CLI to feel professional is lower than a TUI, but the principles are settled. Most "this CLI is bad" reactions trace to violating items on this checklist.

**Contents:**
- [Foundational principles](#foundational-principles)
- [Input and arguments](#input-and-arguments)
- [Output design](#output-design)
- [Exit codes](#exit-codes)
- [Error messages](#error-messages)
- [Help and discoverability](#help-and-discoverability)
- [Subcommands](#subcommands)
- [Configuration and state](#configuration-and-state)
- [Performance and signals](#performance-and-signals)
- [Future-proofing](#future-proofing) · [Naming](#naming)
- [Concrete exemplars to study](#concrete-exemplars-to-study)
- [Final checklist](#final-checklist)

---

## Foundational principles

**Human-first, machine-friendly.** Default output is readable; machine output is opt-in (`--json`, `--plain`, `-o yaml`).

**Composable.** Honor stdin/stdout/stderr, exit codes, signals, and line-based text. Doug McIlroy: *"expect the output of every program to become the input to another, as yet unknown, program."*

**Discoverable.** GUIs put options on screen; CLIs compensate with help text, examples, "did you mean…?" suggestions, and shell completions.

**Conversational and consistent** across tools — same flag names mean the same things.

**Robust and empathetic** — validate input early, fail fast, never lie about state.

**Always use a real argument-parsing library** (Cobra, urfave/cli, Click, Typer, argparse, clap, oclif, picocli, swift-argument-parser). Hand-rolled parsers always get edge cases wrong.

---

## Input and arguments

### Argument syntax

POSIX utility argument syntax:
- Lowercase 2–9 char names.
- Options begin with `-` and a single alphanumeric character.
- `-abc` ≡ `-a -b -c` (combined boolean flags).
- `-o file` or `-ofile` (optionally combined with arg).
- `--` ends option parsing (rest are positional).
- Bare `-` means stdin/stdout.

GNU extensions (now near-universal):
- Long options (`--verbose`, `--output=foo.txt`).
- Every short option has a long counterpart.

**Reserve single letters for the most common flags only.** `-f`/`--file`, `-o`/`--output`, `-v`/`--verbose`, `-q`/`--quiet`, `-h`/`--help`. If users will type it daily, give it a short form. If they'll type it monthly, long-only is fine. Beware `-f`: real-world tools split between `--file` (tar, make) and `--force` (rm, git push) — pick one meaning per tool and never use it for both.

### Flags vs positional args

Prefer flags when meaning is ambiguous. Heroku's example: `heroku fork --from FROMAPP --to TOAPP` is clearer than `heroku fork FROMAPP --app TOAPP`. The clig.dev rule: *"Two or more args of different types is suspect; three is never good."*

### Stdin / stdout / stderr discipline

- **stdout** = primary output (the result; machine-readable when piped).
- **stderr** = secondary channel (logs, progress, prompts, errors).
- Support `-` for stdin/stdout where it makes sense.
- If stdin is a TTY but your program expects piped input, **show help instead of hanging** (avoid `cat` UX).

### Interactivity

Only prompt when stdin is a TTY (`isatty(0)`). When piped or in CI, fail with a message naming the flag the user should pass. Honor `--no-input`. Confirm destructive actions; allow `-y`/`--yes` or `-f`/`--force` to override. For severe actions, require typed confirmation (`--confirm=name-of-thing`).

**Never accept secrets via `--password=…`** — leaks via `ps`, shell history, `docker inspect`, debug logs. Use:
- `--password-file path/to/secret`
- `--password-stdin` (read from stdin)
- OS keychains (macOS Keychain, libsecret, Windows Credential Manager)
- `git-credential-*` helpers

---

## Output design

### Tables for humans

- One record per line.
- **No ASCII borders** — they break `wc -l` and `grep` pipelines.
- Headers by default, with `--no-headers` toggle.
- Truncate to terminal width with `--no-truncate` toggle.
- Allow `--columns col1,col2`, `--sort col`, `--filter`.
- Recommend `--csv` or `--json` for machines.

### JSON / NDJSON

`--json` for structured output. **NDJSON** (one JSON object per line) is more pipe-friendly than a single array — downstream tools can `jq` line-by-line.

`kubectl`'s `-o {wide,json,yaml,name,jsonpath=…,go-template=…,custom-columns=…}` is the gold standard projection system. Adopt it for tools with structured data.

### Verbosity

- `-q` / `--quiet` — suppress non-essential output (errors still print).
- `-v` / `--verbose` — chatty mode.
- `-vv` / `-vvv` — progressive debug levels.
- `--debug` (or `DEBUG=1` env var) for stack traces — never appear by default.

### Progress

Write progress to **stderr**, not stdout (so it doesn't pollute piped output). Suppress all animations when not a TTY. Show progress within ~100ms of starting work — earlier feels twitchy, later feels frozen.

For multi-step work: hide noisy logs behind a progress indicator while things succeed; print them if something fails (Docker Compose pattern). This keeps the success case clean and the failure case debuggable.

### Color

**Disable color when:**
- stdout/stderr is not a TTY, or
- `NO_COLOR` env var is set ([no-color.org](https://no-color.org)), or
- `TERM=dumb`, or
- `--no-color` / `--color=never` is passed.

**Force color** when `FORCE_COLOR=1` is set or `--color=always` is passed.

Provide `--color={auto,always,never}` (auto is default) plus tool-specific overrides like `MYAPP_NO_COLOR` / `MYAPP_FORCE_COLOR`.

Use color sparingly: red for errors, dim for secondary text, bold for headings, cyan/blue for paths. **Never color-only** signaling — pair with a word or symbol.

### Unicode and emoji

Glyphs like ✅, ❌, ⚠ clarify state — yubikey-agent and starship use them well. But:
- Detect locale and `TERM`; fall back to ASCII (`[ok]`, `[!]`, `[X]`) when piped or unsupported.
- Never use emoji as the only signal — pair with words.
- Newer Windows Terminal and macOS/Linux terminals handle emoji fine; older terminals don't.

### Paging

Pipe through `less` (or `$PAGER`) **only when stdout is a TTY**. The standard flags: `LESS=FIRX` (or `less -FIRX`):
- `F` — exit immediately if content fits one screen.
- `I` — case-insensitive search.
- `R` — pass through ANSI color codes.
- `X` — don't clear the screen on exit (leaves content in scrollback).

`bat`, `git`, `gh` all do this. Honor `$PAGER` and `$BAT_PAGER`/`$GIT_PAGER`-style overrides.

---

## Exit codes

### Universal conventions

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | General failure |
| 2 | Misuse / usage error (per BSD convention) |

### Shell-defined

| Code | Meaning |
|---|---|
| 126 | Found but not executable |
| 127 | Command not found |
| 128 + N | Terminated by signal N (130 = SIGINT/Ctrl-C, 143 = SIGTERM, 137 = SIGKILL) |

### BSD `sysexits.h` (richer signaling)

| Code | Constant | Meaning |
|---|---|---|
| 64 | EX_USAGE | Bad command-line usage |
| 65 | EX_DATAERR | Bad input data |
| 66 | EX_NOINPUT | Cannot open input file |
| 69 | EX_UNAVAILABLE | Service unavailable |
| 70 | EX_SOFTWARE | Internal software error |
| 73 | EX_CANTCREAT | Cannot create output |
| 74 | EX_IOERR | I/O error |
| 75 | EX_TEMPFAIL | Temporary failure (retryable) |
| 77 | EX_NOPERM | Permission denied |
| 78 | EX_CONFIG | Configuration error |

Tool-specific overloads are common: `grep`/`rg` use `0` = match found, `1` = no match, `2` = error. Document your scheme in `--help`.

---

## Error messages

The 12-Factor anatomy:

1. **State what was attempted.**
2. **State what failed and why.**
3. **Suggest how to fix it** — give a command if possible.
4. **Link to docs.**

Example:

```
$ myapp dump -o myfile.out
Error: EPERM — invalid permissions on myfile.out
Cannot write to myfile.out; the file is read-only.
Fix with: chmod +w myfile.out
See: https://github.com/jdxcode/myapp#permissions
```

**Catch expected errors and rewrite** — never expose raw stack traces by default. Stack traces only on `--debug` or `DEBUG=1`.

**Put the most important info last.** The eye lands at the bottom of the output. The fix command should be the last line.

**Group repeated errors.** If 100 files fail to parse, summarize: "100 files failed to parse — first three: …; pass `--show-all-errors` to list all."

**"Did you mean…?"** suggestions on typos. Brew, Heroku, Cargo, Git, npm all do this. Suggest, don't auto-execute.

---

## Help and discoverability

### What must show help

All of these must show help:
- `mycli` (no args, when there's no sensible default action)
- `mycli -h`
- `mycli --help`
- `mycli help`
- `mycli sub -h`, `mycli help sub`

`-h` / `--help` is reserved. Don't use it for anything else.

### Concise help by default

When run with no args (and no sensible default action), show:
- One-sentence description.
- 1–2 examples.
- Top-level flags / subcommands list.
- "Run `mycli --help` for more."

`jq`'s no-arg behavior is canonical.

### Full help (`--help`)

- **Synopsis** with POSIX notation: `mycli [-v] [--output FILE] FILE...`.
- **Description** — 1–3 paragraphs.
- **Flags grouped by purpose.** `gh` and Heroku group: General, Output, Filtering, Auth. This scales much better than one alphabetical list.
- **Examples at the end**, building from simple to complex. Examples are the most-read part of help text.
- Link to docs, man page, or `mycli help <topic>`.

### Man pages

Power users love them. Generate from Markdown via `ronn` or `pandoc`. Route `git help foo` and `npm help foo` to the corresponding man page.

### Versioning

Support `--version`, `-V`, and `version` subcommand. Output:
- Semver version.
- Git commit (short SHA).
- Build date.
- Runtime info (Go/Node/Python version).

These end up in bug reports — make them easy to copy. If your tool talks to a server, send the version in the `User-Agent` header.

### Shell completions

Generate for bash, zsh, fish, pwsh. Most modern frameworks (Cobra, Click/Typer, clap, commander, yargs, oclif, picocli) emit them automatically. Wire them up.

Flags should autocomplete. Argument values where possible: `kubectl` completes resource names from the API; `gh` completes repos and PRs; `git` completes branches and tags.

---

## Subcommands

Two patterns:

1. **Single-command** — `grep`, `cp`, `rg`. Simple tools.
2. **Multi-command** — `git foo`, `gh foo`, `docker foo`. Tools with many objects.

For multi-command, **clig.dev recommends noun-verb**:
- `docker container create` (noun-verb), not `docker create container`.
- `gh pr list`, `gh issue close`, `gh repo clone`.

Noun-verb scales: adding `pr review` doesn't conflict with `issue review`. Verb-first runs out of namespace.

**Same flag = same meaning across subcommands.** `-o` should always mean output file (or always output format), never both.

**No catch-all default subcommand.** Don't make `mycli foo` silently mean `mycli run foo` — it's a footgun when you add a future `foo` subcommand.

**No prefix-matching.** `mycli ins` → `install` becomes a breaking change when you add a future `instance` command. Define explicit aliases instead.

**Avoid near-synonyms.** `update` vs `upgrade` confuses users. Pick one.

---

## Configuration and state

### Precedence (highest wins)

1. Command-line flags.
2. Environment variables.
3. Project-local config (`./mytool.toml`, `./.mytoolrc`).
4. User config (`$XDG_CONFIG_HOME/mytool/`).
5. System config (`/etc/mytool/`).
6. Built-in defaults.

This is what `git`, `docker`, `kubectl` all use. Predictable.

### XDG Base Directory Specification

| Variable | Default | Purpose |
|---|---|---|
| `XDG_CONFIG_HOME` | `~/.config` | User config |
| `XDG_DATA_HOME` | `~/.local/share` | Persistent user data |
| `XDG_STATE_HOME` | `~/.local/state` | Logs, history, ephemeral state |
| `XDG_CACHE_HOME` | `~/.cache` | Regenerable cache |
| `XDG_RUNTIME_DIR` | (no default) | Sockets, pipes, mode 0700 |

**Use `~/.config/mytool/`, not `~/.mytool/`.** Older "dotfile in $HOME" pollution is being phased out — adopt XDG for new tools.

On Windows: `%APPDATA%\mytool` for config, `%LOCALAPPDATA%\mytool` for cache. On macOS, prefer XDG (`~/.config/mytool/`) for developer CLIs — it keeps dotfiles portable across machines; reserve `~/Library/Application Support/` for GUI-style apps.

### Environment variables

- Prefix `TOOL_FOO_BAR` (uppercase, underscores).
- Single-line values only.
- Honor general-purpose vars:

| Variable | Purpose |
|---|---|
| `NO_COLOR` | Disable color |
| `FORCE_COLOR` | Force color |
| `DEBUG` | Enable debug output |
| `EDITOR` / `VISUAL` | Preferred text editor |
| `PAGER` | Preferred pager |
| `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` | Proxy settings |
| `TMPDIR` | Temp directory |
| `HOME` | User home |
| `SHELL` | Login shell |
| `TERM` | Terminal type |
| `LINES` / `COLUMNS` | Terminal size |
| `LANG` / `LC_*` | Locale |

### Secrets — what NOT to do

Never accept secrets via `--password=`, `--token=`, etc. on the command line. They leak through:
- `ps` output.
- Shell history files.
- `docker inspect`, `systemctl show`.
- Crash dumps and debug logs.
- Process accounting.

**Use instead:**
- Credential files with restrictive permissions.
- Stdin (`--password-stdin`).
- AF_UNIX sockets.
- OS keychains (gh uses macOS Keychain / libsecret / Windows Credential Manager).
- `git-credential-*`-style helper protocols.

---

## Performance and signals

### Startup time

- **<100ms** — feels instant. `starship` is obsessive about this; it has to be (runs on every prompt).
- **100–500ms** — fast.
- **500ms–2s** — annoying.
- **2s+** — users avoid the tool.

Tactics:
- Lazy-load subcommand modules (oclif's architecture).
- Skip auto-update checks except occasionally (e.g., once a day on a background goroutine).
- Cache parsed config.
- Prefer compiled languages (Go, Rust) over Python/Node for shell-prompt-tier performance.

### Streaming

Stream line-by-line where possible (`grep`, `jq`, `rg`). Don't read whole input before outputting. Flush stdout on newlines so piped consumers see data immediately.

### Signals

| Signal | Convention |
|---|---|
| **SIGINT** (Ctrl-C, exit 130) | Acknowledge immediately, bound cleanup with timeout, exit. **Second Ctrl-C should force-exit.** |
| **SIGTERM** (exit 143) | Graceful shutdown. |
| **SIGPIPE** | When piping into `head` and the consumer closes early. **Exit silently with code 0 or 141; never emit a stack trace.** |
| **SIGHUP** | Long-running daemons reload config; one-shot tools exit. |

**SIGPIPE handling per language:**
- **Python**: `signal.signal(signal.SIGPIPE, signal.SIG_DFL)` at startup.
- **Rust**: handle `ErrorKind::BrokenPipe` explicitly.
- **Go**: ignore `EPIPE` on stdout.
- **Node**: handle `EPIPE` on `process.stdout`.

### Atomicity and idempotency

- Write tmpfile then `rename(2)` — atomic on most filesystems.
- `--dry-run` for destructive operations (`rsync`, `terraform plan`, `git add -n`).
- Re-running should converge ("crash-only" design). The user shouldn't fear running the command twice.
- Configurable timeouts, exponential backoff, retry on `EX_TEMPFAIL` (75) errors.

---

## Future-proofing

Once shipped, your CLI is an API. Users script around it.

- **Additive changes only** when possible.
- **Deprecation runway**: warn for at least one release cycle before removing.
- **Output for humans is iterable**; **machine output (`--json`, `--plain`) must be stable** — that's the contract scripts depend on.
- Document deprecations clearly. Print a notice to stderr: "`--old-flag` is deprecated; use `--new-flag` instead. Will be removed in v2.0."

---

## Naming

- Lowercase, short, easy to type with both hands.
- Memorable but not too generic.
- No mixed case (`curl` ✅, `DownloadURL` ❌).
- Hyphens between words for multi-word names (`gh-actions-helper`, not `gh_actions_helper`).
- Don't reuse existing tool names — `git` is taken.

---

## Concrete exemplars to study

- **gh** — clean noun-verb subcommands; `--json field1,field2` + `--jq '...'` + `--template '...'`; OS-keychain credentials; auto-pages.
- **rg** (ripgrep) — smart defaults (`gitignore`, skip binary, recurse, smart-case); `--json` emits NDJSON; `RIPGREP_CONFIG_PATH` for persistent flags; exit 0/1/2 for found/not-found/error; linear-time regex.
- **fd** — regex by default, colorized, gitignore-aware; `-x cmd {}` simpler than `find -exec`.
- **bat** — TTY-aware (colorizes/pages on terminal, plain `cat` when piped); `--plain`/`-p`; honors `$BAT_PAGER`/`$PAGER`.
- **jq** — tiny startup; `-r` raw output, `-c` compact NDJSON, `-s` slurp; help-on-empty-invocation.
- **httpie / xh** — human-friendly HTTP; pretty on TTY, raw on pipe; xh exists specifically to fix httpie's startup latency.
- **kubectl** — rich `-o` (`json`, `yaml`, `wide`, `name`, `jsonpath`, `go-template`, `custom-columns`); tab completion from API; `--dry-run=client|server`.
- **docker** — multi-level subcommands; parallel per-layer progress bars during pulls; backward-compat aliases (`docker ps` ≡ `docker container ls`).
- **delta** — side-by-side diff via git's `core.pager`; demonstrates plug-in via stdin.
- **eza** (formerly exa) — defaults closer to `ls -lh --color`; git status integration; `--tree`.
- **starship** — cross-shell prompt; sub-100ms hard requirement; single TOML config.

---

## Final checklist

A good CLI:

**Exit & streams**
- Returns 0 on success, non-zero on failure.
- Sends primary output to stdout, messages and errors to stderr.
- Reads `-` as stdin; honors `--`.
- Exits cleanly on SIGPIPE (no stack trace).
- First Ctrl-C graceful, second force.

**Help & versioning**
- Shows help on no-arg / `-h` / `--help` / `help` (subcommand or global).
- Help has synopsis, grouped flags, and examples at the end.
- Ships shell completions and `--version` with semver + commit.

**Flags**
- Every short flag has a long form.
- Uses standard names (`--quiet`, `--verbose`, `--output`, `--force`, `--dry-run`, `--json`, `--no-color`).
- Prefers flags to args when ambiguous.
- Distinct exit codes for distinct failure classes.

**Output**
- Human-friendly by default; `--json` / `--plain` for scripts.
- Tables have no borders and toggleable headers.
- Color auto-detects TTY and honors `NO_COLOR` / `FORCE_COLOR` / `TERM=dumb`.
- No animations when not a TTY.
- No log-level prefixes in default mode.

**Errors**
- State what / why / how-to-fix.
- Suggests "did you mean…?" without auto-running.
- No stack traces unless `--debug`.

**Interactivity**
- Prompts only on TTY.
- Honors `--no-input`.
- Confirms destructive ops with `--yes` / `--force` override.
- No secrets via flag.

**Configuration**
- Precedence: flag > env > config > default.
- Uses XDG dirs.
- Env vars prefixed `MYTOOL_…`.

**Performance**
- Cold start <500ms (ideally <100ms for shell-prompt-tier).
- Streams output line-by-line.
- `--dry-run` for destructive ops.
- Atomic writes; idempotent re-runs.

**Subcommands**
- No catch-all default subcommand.
- No prefix-matching.
- Same flags mean the same things across subcommands.

**Future-proofing**
- Machine output is stable.
- Deprecations carry a release-cycle warning before removal.

---

If the tool grows to need a full-screen UI later, that's a TUI — return to the main `SKILL.md` and pick an ecosystem reference. Many great tools (`gh`, `helix`, `atuin`, `posting`) ship both a CLI and a TUI from the same core, with the CLI handling scripts and the TUI handling exploration.
