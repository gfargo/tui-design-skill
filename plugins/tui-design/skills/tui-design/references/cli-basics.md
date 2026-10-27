# Simple CLI design — non-TUI command-line tools

For programs that don't have a full-screen UI: read args, do work, print output, exit. This document synthesizes [clig.dev](https://clig.dev), the [12-Factor CLI](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46) principles, POSIX.1-2024 utility conventions, GNU coding standards, the XDG Base Directory Specification, BSD `sysexits.h`, and the design of widely admired CLIs (`gh`, `rg`, `fd`, `bat`, `jq`, `httpie`, `kubectl`, `docker`, `starship`).

The bar for a CLI to feel professional is lower than a TUI, but the principles are settled. Most "this CLI is bad" reactions trace to violating items on this checklist.

**Contents:**
- [Foundational principles](#foundational-principles)
- [Input and arguments](#input-and-arguments)
- [Output design](#output-design)
- [Exit codes](#exit-codes)
- [Error messages](#error-messages)
- [Help and discoverability](#help-and-discoverability) (includes [shell completions](#shell-completions) and [demo recordings](#demo-recordings))
- [Subcommands](#subcommands)
- [Shell integration](#shell-integration)
- [Configuration and state](#configuration-and-state)
- [Performance and signals](#performance-and-signals) (includes Windows)
- [Testing one-shot CLIs](#testing-one-shot-clis)
- [Future-proofing](#future-proofing)
- [Shipping, updates, and telemetry](#shipping-updates-and-telemetry)
- [Naming](#naming)
- [Concrete exemplars to study](#concrete-exemplars-to-study)
- [Final checklist](#final-checklist)

---

## Foundational principles

**Human-first, machine-friendly.** Default output is readable; machine output is opt-in (`--json`, `--plain`, `-o yaml`). **Composable:** honor stdin/stdout/stderr, exit codes, signals, and line-based text. **Discoverable:** help text, examples, "did you mean…?" suggestions, and shell completions. **Consistent and robust:** the same flag names mean the same things across tools; validate input early, fail fast, never lie about state.

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

Prefer flags when meaning is ambiguous. Heroku's example: `heroku fork --from FROMAPP --to TOAPP` is clearer than `heroku fork FROMAPP --app TOAPP`. Jeff Dickey's [12 Factor CLI Apps](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46) rule of thumb, which clig.dev cites: one type of argument is fine, two types are suspect, three are never good.

### Stdin / stdout / stderr discipline

- **stdout** = primary output (the result; machine-readable when piped).
- **stderr** = secondary channel (logs, progress, prompts, errors).
- Support `-` for stdin/stdout where it makes sense.
- If stdin is a TTY but your program expects piped input, **show help instead of hanging** (avoid `cat` UX).

### Interactivity

Prompt only when an interactive input channel is available—normally a TTY, or an explicitly opened `/dev/tty` for a composable picker. When input is piped or the process is in CI, fail with a message naming the documented flag, environment variable, or stdin contract that makes the operation non-interactive; there is no universal `--no-input` spelling. Confirm destructive actions; allow a documented `-y`/`--yes` or `-f`/`--force` override. For severe actions, require typed confirmation (`--confirm=name-of-thing`).

**Cancelling a prompt (Ctrl-C, or Esc where the prompt library maps it) is an abort, not success: restore the terminal and exit 130**, the same code a shell reports for SIGINT (128 + 2). Exit 0 would let `mytool init && mytool deploy` carry on with no answer. A real SIGINT is different; see *Signals*.

Never accept a secret as a flag value; see *Secrets — what NOT to do*.

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

`--json` for structured output.

- **Bounded results: one document. Unbounded or streaming results: NDJSON** (one compact object per line, nothing else on stdout), so downstream tools can `jq` line by line. Pretty-print only on a TTY.
- **The schema is additive.** Add fields; never remove, rename, retype, or repurpose one, and have consumers ignore unknown fields (Terraform's JSON format states this rule). Times are RFC 3339 UTC with a `Z` (`2026-04-29T15:25:16Z`). Numbers are JSON numbers, never `"1.2 MB"` or `"1,234"`.
- **Errors under `--json`.** No convention is settled (npm prints `{"error":{…}}` on stdout, the AWS CLI's `--cli-error-format json` writes to stderr, and gh, cargo, and kubectl emit no structured errors). Pick stderr so stdout stays result-only: one compact line, empty stdout, the same non-zero exit as the human error, and a stable `code` that scripts branch on:

```
{"schema_version":1,"error":{"code":"permission_denied","message":"cannot write out.txt: permission denied","hint":"chmod +w out.txt"}}
```

  Version the error object with the success schema, and keep stack traces out of it unless `--debug` is on.

`kubectl`'s `-o {wide,json,yaml,name,jsonpath=…,go-template=…,custom-columns=…}` is the gold standard projection system. Adopt it for tools with structured data.

### Verbosity

- `-q` / `--quiet` — suppress non-essential output (errors still print).
- `-v` / `--verbose` — chatty mode.
- `-vv` / `-vvv` — progressive debug levels.
- `--debug` (or `MYTOOL_DEBUG=1`) for stack traces — never appear by default. Don't read plain `DEBUG`: Node's `debug` package owns it, so `DEBUG=*` set for another tool would flood yours, and `DEBUG=1` matches nothing there.

### Progress

Write progress to **stderr**, not stdout (so it doesn't pollute piped output). Suppress all animations when not a TTY. Start showing progress once work has run for roughly 100–200ms: an indicator that flashes for near-instant work feels twitchy, and silence past a few hundred milliseconds feels frozen. The same delayed-spinner rule is spelled out in `references/visual-patterns.md` → *Spinners*.

For multi-step work, hide noisy logs behind a progress indicator while things succeed and print them if something fails (the Docker Compose pattern).

### Color

**Decide per stream.** Color stdout by whether stdout is a TTY and stderr by whether stderr is, so `mytool | less` keeps colored errors and `mytool 2>err.log` stays plain ([clig.dev](https://clig.dev/#output)).

**Disable color when:**
- that stream is not a TTY, or
- `NO_COLOR` env var is set to a non-empty value ([no-color.org](https://no-color.org)), or
- `TERM=dumb`, or
- `--no-color` / `--color=never` is passed.

**Force color** when `FORCE_COLOR` is set (in the chalk/supports-color convention, `FORCE_COLOR=0` instead forces color *off*) or `--color=always` is passed. Treat `CLICOLOR_FORCE` ([bixense.com/clicolors](https://bixense.com/clicolors/)) as another force signal, still subordinate to `NO_COLOR`; some older tools read `CLICOLOR=0` as off.

Provide `--color={auto,always,never}` (auto is default) plus tool-specific overrides like `MYAPP_NO_COLOR` / `MYAPP_FORCE_COLOR`. Define precedence instead of leaving conflicts accidental:

- Order: explicit CLI flag → tool-specific env → general env → automatic TTY/capability detection.
- At the same level a disable signal wins: with both `NO_COLOR` and `FORCE_COLOR` set, disable color unless an explicit `--color=always` overrides them.
- Runtimes split here: Python 3.13 lets `NO_COLOR` win, while Node.js and [force-color.org](https://force-color.org/) let `FORCE_COLOR` win (force-color.org treats any non-empty value, even `0`, as on). Document your order and test both variables together.

Use color sparingly: red for errors, dim for secondary text, bold for headings, cyan/blue for paths. **Never color-only** signaling — pair with a word or symbol.

### Unicode and emoji

Glyphs like ✅, ❌, ⚠ clarify state, but detect locale and `TERM`, fall back to ASCII (`[ok]`, `[!]`, `[X]`) when piped or unsupported, and never use emoji as the only signal.

### Paging

Pipe through `less` (or `$PAGER`) **only when stdout is a TTY**, and never page `--json` or other machine output. Set `LESS=FRX` only when `LESS` is unset, as git does (its `FRX` default is applied only if the variable is unset): `F` exits immediately if content fits one screen, `R` passes ANSI color through, `X` leaves content in scrollback on exit. Never override a `LESS` the user set. Honor `$PAGER` and `$BAT_PAGER`/`$GIT_PAGER`-style overrides.

### Pagination for API-backed lists

Give list commands a documented `--limit N` with a finite default and a way to see the rest (`--paginate`, or a cursor in the output). When the limit cut results off, say so on **stderr** with the flag that fixes it, and exit 0, since truncating on request is not an error:

```
$ mytool list --limit 30 > items.txt
note: showing 30 of 1040 items; pass --limit N or --paginate for more
```

gh bounds by default (`--limit` 30) and truncates silently when piped; the AWS CLI fetches every page by default and `--max-items` adds a `NextToken`. Pick one design per tool. Under `--json`, put the cursor in the document (`{"items":[…],"next_cursor":"…"}`) or, for NDJSON, use only the stderr note.

---

## Exit codes

### Default scheme

| Code | Use |
|---|---|
| 0 | Success |
| 1 | Failure with no more specific code |
| 2 | Usage error (bad flag or argument). Not universal, but bash builtins, argparse, clap, and Go's `flag` use it |
| 3–123 | Your documented domain codes. The status is 8 bits, so `exit(256)` is success: clamp computed codes |
| 124–128 | Not yours: `timeout` uses 124 and 125, the shell uses 126 (not executable), 127 (not found), and 128 |
| 129–255 | Not yours: 128 + N means killed by signal N (130 SIGINT, 137 SIGKILL, 143 SIGTERM), and 255 makes `xargs` stop |

Document your codes in `--help`.

### BSD `sysexits.h` (legacy, nonportable richer signaling; codes 64–78 fit the scheme above)

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

Tool-specific overloads are common: `grep`/`rg` use `0` = match found, `1` = no match, `2` = error.

Treat `sysexits.h` as a legacy compatibility vocabulary, not a cross-platform recommendation. Many modern tools use a smaller documented scheme instead. Adopt it whole or not at all: if you do, `EX_TEMPFAIL` (75) is your retryable-failure code; if you don't, document which of your own codes callers may retry.

---

## Error messages

The 12-Factor anatomy:

1. **State what was attempted.**
2. **State what failed and why.**
3. **Link to docs** when there is more to read (before the hint).
4. **Suggest how to fix it** — give a command if possible, as the last line.

Example, with a bad version for contrast:

```
good:  error: cannot write out.txt: permission denied
       hint: chmod +w out.txt
bad:   ERROR [2026-10-27T05:10:18Z] Failed!!
```

Say what and why in one lowercase line with no trailing period, name the object, and end with the fix. `hint:` is git's spelling and `help:` is cargo's; pick one. A program-name prefix (`mytool: error: …`, as argparse prints) is fine when your stderr is interleaved with other tools, but then use it on every line.

**One format rule.** Start the message that is itself the failure with a plain-word `error:` (and a warning with `warning:`), so a reader, a screen reader, or `grep` can tell what the line is. Do not print log-style `ERR`/`WARN`/`[ERROR]` labels, timestamps, or any prefix on ordinary output unless `--verbose` or `--debug` is on ([clig.dev](https://clig.dev/#output) rules out log-level labels, not a plain-word failure marker). Other references defer to this rule.

**Catch expected errors and rewrite** — never expose raw stack traces by default. Stack traces only on `--debug` or `MYTOOL_DEBUG=1`.

**Put the most important info last** ([clig.dev](https://clig.dev/#errors)). The eye lands at the bottom of the output. The fix command is the last line; when there is no fix command, the docs link is.

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
- **Commands and flags grouped by purpose.** `gh --help` groups commands (Core, GitHub Actions, Additional) while its per-command flags stay one flat list; for a long flag list, add headings such as Output, Filtering, Auth. Grouping scales much better than one alphabetical list.
- **Examples first, right after the description**, building from simple to complex. [clig.dev](https://clig.dev/#help) says users read examples before any other documentation, so show them first and move a long set to `help <topic>` or the docs. `gh` puts its examples last, which only works while the flag list is short enough to keep them on screen.
- Link to docs, man page, or `mycli help <topic>`.

A literal template (stdout, exit 0, for `-h` and `--help`):

```
Sync local files to a bucket.

Usage: mytool [OPTIONS] <COMMAND>

Examples:
  mytool push ./dist s3://site     Upload a directory
  mytool pull s3://site --dry-run  Preview a download

Commands:  push, pull, status
Options:   -o, --output <text|json>  -q, --quiet  -h, --help
Docs: https://example.com/mytool
```

### Man pages

Power users love them. Generate them from the same command tree as `--help`, in the release build, and ship them in the package: Cobra's `doc.GenManTree`, `clap_mangen`, `click-man`, or `argparse-manpage` (Typer has no generator; feed `typer.main.get_command(app)` to `click-man` and re-test on upgrade). Otherwise write Markdown and convert with `ronn` or `pandoc`. Route `git help foo` and `npm help foo` to the corresponding man page.

### Versioning

Support `--version`, `-V`, and `version` subcommand. The first line is `mytool 1.2.3` on stdout with exit 0, and it makes no network call. Detail lines may follow:
- Git commit (short SHA).
- Build date.
- Runtime info (Go/Node/Python version).

These end up in bug reports — make them easy to copy. If your tool talks to a server, send the version in the `User-Agent` header.

### Shell completions

Generate for bash, zsh, fish, pwsh where the parser allows. Cobra, Click (PowerShell from 8.5), and Typer generate all four from the command definition; yargs documents bash, zsh, and fish but not PowerShell, and picocli's `AutoComplete` targets only bash and zsh. clap needs the `clap_complete` crate and oclif needs `@oclif/plugin-autocomplete`; commander has no built-in support ([commander.js#2008](https://github.com/tj/commander.js/issues/2008)), so add a completion package or write the scripts. Wire them up.

Flags should autocomplete. Argument values where possible: `kubectl` completes resource names from the API; `gh` completes repos and PRs; `git` completes branches and tags.

- **Contract:** `mytool completion <bash|zsh|fish|pwsh>` prints the script to stdout and writes nothing. Document where each shell loads it from: bash `~/.local/share/bash-completion/completions/mytool` (`/etc/bash_completion.d` is the legacy eager directory), zsh a file named `_mytool` in a directory on `$fpath` before `compinit`, fish `~/.config/fish/completions/mytool.fish`.
- **Dynamic values** go through the framework's hook, which runs your binary on every Tab press: Cobra's hidden `__complete` ([docs](https://github.com/spf13/cobra/blob/v1.10.2/site/content/completions/_index.md)); Click `_MYTOOL_COMPLETE=<shell>_source` ([docs](https://github.com/pallets/click/blob/8.5.0/docs/shell-completion.md)) and Typer `source_<shell>`, with a Click PowerShell script only from 8.5; clap's `COMPLETE=<shell>`, which `clap_complete` still gates behind `unstable-dynamic` (static `generate()` is stable).
- **Keep the hook fast and pure:** no prompts, no file writes, nothing on stdout but candidates; time-box and cache network lookups, and return no candidates on failure.

### Demo recordings

For screenshots and demo GIFs of a CLI or TUI, use the `vhs-cli-demos` skill when it is installed. Otherwise record with [VHS](https://github.com/charmbracelet/vhs), which needs `ttyd` and `ffmpeg` on `PATH`:

- Script the scene in a `.tape` file and render it with `vhs demo.tape`. `vhs new demo.tape` writes a starter tape; `vhs record > demo.tape` captures a live session to edit.
- Pin everything that changes the frame: `Set Columns` and `Set Rows` (VHS 0.12+; older releases take pixel `Width`/`Height`) at a size whose layout you have tested, `Set FontSize`, `Set Theme`, and `Env` for other inputs such as `TZ` or `LANG`.
- Put setup and cleanup between `Hide` and `Show`, wait for slow output with `Wait+Screen /regex/` instead of a guessed `Sleep`, and declare each program the tape needs with `Require` so a missing one fails before recording.
- `Screenshot demo.png` captures a still and `Output demo.gif` records motion. Shrink GIFs losslessly with `gifsicle -O3` before publishing; `charmbracelet/vhs-action` regenerates them in CI.

---

## Subcommands

Single-command tools (`grep`, `cp`, `rg`) are simple; multi-command tools (`git`, `gh`, `docker`) fit many objects. For multi-command tools, **noun-verb** is the more common order (clig.dev says either order works, but noun-verb "seems to be more common"):
- `docker container create` (noun-verb), not `docker create container`.
- `gh pr list`, `gh issue close`, `gh repo clone`.

Noun-verb scales: adding `pr review` doesn't conflict with `issue review`. Verb-first runs out of namespace.

**Same flag = same meaning across subcommands.** `-o` should always mean output file (or always output format), never both.

**No catch-all default subcommand.** Don't make `mycli foo` silently mean `mycli run foo` — it's a footgun when you add a future `foo` subcommand.

**No prefix-matching.** `mycli ins` → `install` becomes a breaking change when you add a future `instance` command. Define explicit aliases instead.

**Avoid near-synonyms.** `update` vs `upgrade` confuses users. Pick one.

---

## Shell integration

A child process cannot change its parent shell's working directory or environment variables — only the shell itself can do that. There's no IPC trick around this; two patterns cover everything real tools need.

### cd-on-exit: the cwd-file wrapper function

If your tool navigates directories and should `cd` the user's shell on exit (a file picker, a directory jumper), ship a flag that writes the final directory to a caller-specified file, and document a shell wrapper function that reads it and `cd`s after your program exits. yazi and ranger converge on the identical shape:

```bash
function y() {
    local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
    command yazi "$@" --cwd-file="$tmp"
    IFS= read -r -d '' cwd < "$tmp"
    [ "$cwd" != "$PWD" ] && [ -d "$cwd" ] && builtin cd -- "$cwd"
    command rm -f -- "$tmp"
}
```

ranger's `--choosedir` does the same thing under a different flag name. This is the pattern, not an implementation detail — there's no other way to get a "cd on exit" TUI.

### The `eval "$(tool init shell)"` pattern

For env vars, keybindings, or functions that need to live in the *current* shell session, ship an `init`/`activate` subcommand that prints shell source for the user to `eval`. What gets emitted varies by need:

- **starship:** a `precmd` prompt-regeneration hook plus a `preexec` hook.
- **zoxide:** `z`/`zi` functions plus a `chpwd` hook that tracks visited directories.
- **atuin:** keybindings (Ctrl-R and the Up arrow by default; `--disable-up-arrow` opts out) plus history-capture hooks.
- **mise:** a wrapper function plus `precmd`/`chpwd` hooks that re-derive and re-export `PATH` on every prompt render and `cd`. It can't set the parent shell's env, so it has the *shell itself* recompute it.
- **fzf:** `--zsh`/`--bash` (since v0.48, replacing an older `install.sh`) emit keybindings and completions from one embedded call.

### Never silently edit rc files

Show the user the line and tell them to add it (`Add this to the end of ~/.zshrc`) — this is what starship, zoxide, and mise all do, and it's the strong convention. Auto-appending via an explicit, visible installer step (atuin's `curl | sh` installer does this) is an accepted variant; silently mutating a user's rc file without telling them is not.

---

## Configuration and state

### Precedence (highest wins)

1. Command-line flags.
2. Environment variables.
3. Project-local config (`./mytool.toml`, `./.mytoolrc`).
4. User config (`$XDG_CONFIG_HOME/mytool/`).
5. System config (`/etc/mytool/`).
6. Built-in defaults.

This is the [clig.dev](https://clig.dev/#configuration) order (flags, env, project, user, system), with built-in defaults as the floor. Predictable.

### XDG Base Directory Specification

| Variable | Default | Purpose |
|---|---|---|
| `XDG_CONFIG_HOME` | `~/.config` | User config |
| `XDG_DATA_HOME` | `~/.local/share` | Persistent user data |
| `XDG_STATE_HOME` | `~/.local/state` | History, logs, recent files — state that persists between restarts |
| `XDG_CACHE_HOME` | `~/.cache` | Regenerable cache |
| `XDG_RUNTIME_DIR` | (no default) | Sockets, pipes, mode 0700 |

**Use `~/.config/mytool/`, not `~/.mytool/`.** Older "dotfile in $HOME" pollution is being phased out — adopt XDG for new tools.

On Windows: `%APPDATA%\mytool` for config, `%LOCALAPPDATA%\mytool` for cache. On macOS, prefer XDG (`~/.config/mytool/`) for developer CLIs — it keeps dotfiles portable across machines; reserve `~/Library/Application Support/` for GUI-style apps. The "native" helpers return that folder and, except `platformdirs` 4.6+, ignore `XDG_CONFIG_HOME`: Go's `os.UserConfigDir`, Rust's `dirs` and `directories`, and `platformdirs` when the variable is unset. Check an absolute `XDG_CONFIG_HOME`, then fall back to `~/.config`, by hand (or use `etcetera` or `xdg`, which already do).

### Explaining where a value came from

Accept `--config PATH` and `MYTOOL_CONFIG` (flag beats env), and give users a command that prints each effective value with its source, redacting secrets, as `git config --show-origin`, `npm config list -l`, and `aws configure list` do:

```
$ mytool config list --show-origin
user   /home/ann/.config/mytool/config.toml   format = "json"
env    MYTOOL_FORMAT                          format = "text"   (wins)
default                                       color  = "auto"
```

### Environment variables

Prefix tool-specific variables `TOOL_FOO_BAR` (uppercase, underscores, single-line values) and honor the general-purpose ones that apply: `NO_COLOR`, `FORCE_COLOR`, and `CLICOLOR_FORCE` (see *Color*), `DO_NOT_TRACK` (see *Telemetry*), `EDITOR`/`VISUAL`, `PAGER`, `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY`, `TMPDIR`, `TERM`, `LINES`/`COLUMNS`, and `LANG`/`LC_*`.

### Secrets — what NOT to do

Never accept secrets via `--password=`, `--token=`, etc. on the command line. They leak through `ps`, shell history, `docker inspect` and `systemctl show`, crash dumps and debug logs, and process accounting.

**Use instead:**
- Credential files with restrictive permissions (`--password-file path/to/secret`).
- Stdin (`--password-stdin`).
- AF_UNIX sockets.
- OS keychains (gh uses macOS Keychain / libsecret / Windows Credential Manager).
- `git-credential-*`-style helper protocols.

### First-run authentication

Two patterns dominate, and both are legitimate:

1. **Browser + OAuth device-code flow**, token written to the OS keychain (`gh auth login`, `vercel login`): open a browser tab, or show a URL and one-time code, and poll until the user approves. Support a non-browser fallback (`--with-token`, a PAT from stdin) for headless use.
2. **Direct prompt for long-lived credentials**, written to a plaintext config file — still standard for access-key-style cloud CLIs (`aws configure`), though AWS is moving federated auth to device flow (`aws configure sso`).

**Before prompting through ordinary stdio, check both stdin and stdout are TTYs** (`isatty()` on both)—gh's auth flow does this. A tool that deliberately opens `/dev/tty` should test that channel instead. **The real cross-ecosystem non-interactive convention is an environment variable that short-circuits the interactive flow**—`GH_TOKEN`, `VERCEL_TOKEN`, and `GH_PROMPT_DISABLED` (any value turns gh's prompts off)—not a flag. There is no settled `--no-input`-style flag name (Django uses `--no-input`, Terraform `-input=false`, git `GIT_TERMINAL_PROMPT=0`, npm and gh none)—don't present one as a standard; fit your tool's existing flag vocabulary and honor `CI=true` as a secondary signal.

**Keychain libraries for OS-native storage:**
- Go — `zalando/go-keyring` (what gh uses) or `99designs/keyring` (no release since 2022; more backends, including an encrypted-file fallback for headless hosts).
- Rust — the `keyring` crate. Python — `keyring` (`PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring` disables it).
- Node — **not `keytar`, archived and unmaintained since December 2022**; VS Code moved to Electron's `safeStorage`, and a plain Node CLI should fall back to a config file.
- On Linux, keychain backends need a running Secret Service daemon (GNOME Keyring/KWallet) that headless containers often lack, so ship an explicit plaintext fallback (gh's opt-in `--insecure-storage`) rather than failing silently.

**If you do fall back to a plaintext file, set the permissions explicitly — don't rely on umask.** AWS CLI shipped this bug (CVE-2026-13769): under a default umask, three subcommands wrote credential files world-readable (0644) instead of 0600. `chmod 600` the file yourself at creation time.

---

## Performance and signals

### Startup time

- **<100ms** — feels instant. `starship` is obsessive about this — it has to be (runs on every prompt) — and bounds each module with `scan_timeout` (30ms) and `command_timeout` (500ms).
- **100–500ms** — fast.
- **500ms–2s** — annoying.
- **2s+** — users avoid the tool.

Tactics: lazy-load subcommand modules (oclif's architecture), run update checks at most daily in the background, cache parsed config, and prefer Go or Rust over Python or Node for prompt-tier speed.

### Streaming

Stream line-by-line where possible (`grep`, `jq`, `rg`). Don't read whole input before outputting. Flush stdout on newlines so piped consumers see data immediately.

### Signals

| Signal | Convention |
|---|---|
| **SIGINT** (Ctrl-C) | Acknowledge immediately, bound cleanup with a timeout, then **re-raise** (below). **A second Ctrl-C should force-exit.** |
| **SIGTERM** (exit 143) | Graceful shutdown. |
| **SIGPIPE** | When piping into `head` and the consumer closes early. **Exit silently with code 0 or 141; never emit a stack trace.** |
| **SIGHUP** | Long-running daemons reload config; one-shot tools exit. |

**Re-raise SIGINT; don't `exit(130)`.** After cleanup, restore the default handler and send SIGINT to yourself, so the parent sees death-by-signal ([Cracauer](https://www.cons.org/cracauer/sigint.html)). Bash aborts a script or `for` loop only when its child died of SIGINT; a child that catches it and exits 130 reads as "handled", and the loop carries on. Verified for Go, Python, Node, and Rust.
- **Go:** `signal.Reset(os.Interrupt)`, then `syscall.Kill(syscall.Getpid(), syscall.SIGINT)` (POSIX only; delivery is asynchronous).
- **Python 3.8+:** let `KeyboardInterrupt` propagate (`finally:` for cleanup, or `except KeyboardInterrupt: cleanup(); raise`); never `sys.exit(130)`.
- **Rust:** `signal_hook::low_level::emulate_default_handler(SIGINT)`. **Node:** remove the listeners, then `process.kill(process.pid, 'SIGINT')`.
- A program that never catches SIGINT already does this (Go without `signal.Notify`, Node without a listener, uncaught Python).

**SIGPIPE handling per language:**
- **Python**: `signal.signal(signal.SIGPIPE, signal.SIG_DFL)` at startup.
- **Rust**: handle `ErrorKind::BrokenPipe` explicitly.
- **Go**: nothing by default. A broken-pipe write to fd 1 or 2 already kills the program with SIGPIPE unless it calls `signal.Notify` for SIGPIPE, in which case the write returns `EPIPE` and you exit quietly on it ([os/signal](https://pkg.go.dev/os/signal#hdr-SIGPIPE)).
- **Node**: handle `EPIPE` on `process.stdout`.

### Windows

- No SIGPIPE, SIGHUP, or 128 + N codes (console close arrives as an event, [`CTRL_CLOSE_EVENT`](https://learn.microsoft.com/en-us/windows/console/handlerroutine)). A write to a closed pipe is a plain write error: exit quietly. Keep your own codes small (0–123), and don't map an unhandled Ctrl+C (status `0xC000013A`) to 130.
- Enable `ENABLE_VIRTUAL_TERMINAL_PROCESSING` before emitting ANSI: Go and Rust do it themselves (`golang.org/x/sys/windows`, `anstyle-query`), Python via `colorama.just_fix_windows_console()`, and Node's tty layer already does.
- The shell doesn't expand globs, so expand them yourself, and emit `\n` only. Windows Terminal sets no `TERM` or `COLORTERM`.

### Atomicity and idempotency

- **Atomic writes:** write a temp file in the *same directory* as the target (a cross-filesystem rename fails), `fsync` it, set the final mode (temp files are 0600), then rename it over the target. Readers and crashes see the old file or the whole new one; the file `fsync` is for durability, and a directory `fsync` makes the entry itself durable. On Windows the replace is best effort, not guaranteed atomic (Go's `os.Rename` isn't atomic there; use Python's `os.replace`, not `os.rename`).
- **Partial results:** never leave a truncated file at the final path. Write atomically, or keep it under an explicit partial name (`.part`, `--partial`) and say so on stderr, and exit non-zero on any incomplete result.
- `--dry-run` for destructive operations (`rsync`, `terraform plan`, `git add -n`).
- Re-running should converge ("crash-only" design). The user shouldn't fear running the command twice.
- Configurable timeouts, exponential backoff, and retries limited to transient failures (`EX_TEMPFAIL` (75) if you use sysexits).

---

## Testing one-shot CLIs

Test the built binary as a black box on three channels: **stdout, stderr, and the exit code**. Add cases for no TTY (the default under a test runner) and for `NO_COLOR`, and keep golden files for text only, not color escapes.

| Stack | Tool |
|---|---|
| Go | [`testscript`](https://github.com/rogpeppe/go-internal/blob/v1.16.0/testscript/doc.go). `! exec` asserts only non-zero, so add a small custom command to check an exact code |
| Rust | `trycmd` (`.toml` and `.trycmd` cases), `snapbox`, or `assert_cmd` |
| Click | `click.testing.CliRunner`: `result.stdout`, `result.stderr`, and `result.output` (interleaved) since Click 8.2 |
| Typer | `typer.testing.CliRunner` (Typer 0.26+ vendors Click) |

```
# testdata/basic.txtar  (testscript)
exec mytool ann
stdout '^hello ann\n$'
! stderr .
! exec mytool bad
! stdout .
stderr '^error: cannot read bad: no such file\n$'
env NO_COLOR=1
exec mytool ann
! stdout '\x1b'
```

```python
r = CliRunner().invoke(cli, ["bad"])
assert (r.exit_code, r.stdout, r.stderr) == (1, "", "error: cannot read bad: no such file\n")
```

---

## Future-proofing

Once shipped, your CLI is an API. Users script around it.

- **Additive changes only** when possible.
- **Deprecation runway**: warn for at least one release cycle before removing.
- **Output for humans is iterable**; **machine output (`--json`, `--plain`) must be stable** — that's the contract scripts depend on.
- Document deprecations clearly. Print a notice to stderr: "`--old-flag` is deprecated; use `--new-flag` instead. Will be removed in v2.0."

---

## Shipping, updates, and telemetry

### Distribution shape constrains your options

- **Compiled binary (Go/Rust) + Homebrew tap**: zero runtime dependency, the dominant pattern for performance-sensitive CLIs (ripgrep, starship, zoxide, atuin). goreleaser's `brews` publisher is deprecated (hard-deprecated in v2.16) in favor of `homebrew_casks`.
- **npm with per-platform `optionalDependencies`** (esbuild, `@swc/core`): each platform gets its own scoped package and the package manager installs only the matching one. It superseded the `postinstall`-downloads-a-binary approach, which breaks under offline installs, custom registries, and `--ignore-scripts`.
- **Pure npm / pipx**: needs the language runtime present, but is the cheapest to publish and update.

### Update-check etiquette

If you check for updates: check async, cache the result (once a day is the norm — both gh and the widely-used `update-notifier` npm package default to a 24-hour interval), and print the notice to stderr *after* your normal output, not interleaved with it. Auto-skip in CI and gate on stdout being a TTY. Provide an opt-out env var (gh's is `GH_NO_UPDATE_NOTIFIER`; the npm package's is `NO_UPDATE_NOTIFIER`).

**Defer to the package manager that installed you.** If a user got your tool via Homebrew, `brew upgrade` should be the update path — don't tell them to self-update through a mechanism the package manager doesn't own. gh compiles its update checker in only under the `updateable` build tag, which the Homebrew formula sets ([update_enabled.go](https://github.com/cli/cli/blob/v2.103.2/internal/ghcmd/update_enabled.go)), and the notice it prints for Homebrew installs says `brew upgrade gh`.

### Telemetry, if you collect it

`DO_NOT_TRACK=1` is a named convention with thin adoption: netdata, tilt, and the GitHub CLI honor it, while Homebrew and Gatsby kept their own variables (`HOMEBREW_NO_ANALYTICS`, `GATSBY_TELEMETRY_DISABLED`) and the .NET SDK has not adopted it (`DOTNET_CLI_TELEMETRY_OPTOUT`; [dotnet/sdk#3917](https://github.com/dotnet/sdk/issues/3917) is still open). So:
- Ship your own opt-out: an env var plus a `tool telemetry disable` subcommand. gh uses `GH_TELEMETRY` and a `telemetry` config key, and `GH_TELEMETRY` overrides `DO_NOT_TRACK`.
- Skip telemetry in CI, and honor `DO_NOT_TRACK=1` as a courtesy; it costs one env lookup.
- Disclose before sending anything. Homebrew shows its analytics notice before the first event, so users can opt out first.
- Treat the opt-out as an absolute veto, checked first, before any event is built.

---

## Naming

Lowercase, short, easy to type with both hands, memorable but not generic, hyphens between words (`gh-actions-helper`), no mixed case (`curl` ✅, `DownloadURL` ❌), and no collision with an existing tool (`git` is taken).

---

## Concrete exemplars to study

- **gh** — noun-verb subcommands; `--json field1,field2` + `--jq` + `--template`; OS-keychain credentials.
- **rg** — smart defaults (`gitignore`, skip binary, recurse); `--json` emits NDJSON; `RIPGREP_CONFIG_PATH`; exit 0/1/2 for found/not-found/error.
- **jq** — tiny startup; `-r`, `-c`, `-s`; help on empty invocation.
- **bat** and **httpie/xh** — pretty on a TTY, plain on a pipe (`--plain`, `$BAT_PAGER`).
- **docker** — multi-level subcommands, per-layer progress bars, backward-compatible aliases (`docker ps` ≡ `docker container ls`).

---

## Final checklist

Answer each before shipping; a "no" points to the section that owns the rule.

- **Streams and signals:** Does the result go to stdout and everything else to stderr, with `-` and `--` honored, and do SIGPIPE and a second Ctrl-C end cleanly? → *Stdin / stdout / stderr discipline*, *Signals*
- **Exit codes:** Does each failure class have a documented code, and does a cancelled prompt exit 130? → *Exit codes*, *Interactivity*
- **Help:** Does every entry point show help, with examples near the top and completions for each shell your parser supports? → *Help and discoverability*
- **Flags and subcommands:** Do flags use standard names with one meaning everywhere, and does the tool avoid catch-all defaults and prefix-matching? → *Argument syntax*, *Subcommands*
- **Output:** Can a script rely on stable machine output while the human default degrades cleanly without a TTY, under `NO_COLOR`, and on `TERM=dumb`? → *Output design*, *Color*
- **Errors:** Does each failure say what, why, and how to fix it, fix last, under a plain `error:` and without a stack trace? → *Error messages*
- **Interactivity and secrets:** Does it prompt only on a TTY, offer a documented non-interactive path, and never take a secret as a flag? → *Interactivity*, *Secrets — what NOT to do*
- **Configuration:** Do precedence, XDG paths, and `MYTOOL_` env names follow the conventions? → *Configuration and state*
- **Performance and safety:** Is cold start within budget, output streamed, destructive work behind `--dry-run`, and writes atomic and idempotent? → *Performance and signals*
- **Tests and platforms:** Do tests pin stdout, stderr, and the exit code with no TTY and under `NO_COLOR`, and does the tool work on Windows? → *Testing one-shot CLIs*, *Windows*
- **Future-proofing:** Will existing scripts survive the next release? → *Future-proofing*

---

If the tool grows to need a full-screen UI later, that's a TUI — return to the main `SKILL.md` and pick an ecosystem reference. Many great tools (`atuin`, `glow`) ship both a CLI and a TUI from the same core, with the CLI handling scripts and the TUI handling exploration.
