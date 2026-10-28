I'd use `clap_complete`'s dynamic `CompleteEnv` mechanism for this. Static script generation (`clap_complete::generate`) can only complete flags, subcommands and fixed value sets. It can't look up values at Tab time. The cost is that dynamic completion is still behind clap_complete's `unstable-dynamic` feature, so you should pin the crate version.

## 1. Wire it up

```toml
[dependencies]
clap = { version = "4", features = ["derive"] }
# Pin exactly: the dynamic API is unstable and can change in a minor release
clap_complete = { version = "=4.5.x", features = ["unstable-dynamic"] }
```

```rust
use clap::{CommandFactory, Parser};
use clap_complete::engine::{ArgValueCandidates, ArgValueCompleter, CompletionCandidate, PathCompleter};
use clap_complete::CompleteEnv;

#[derive(Parser)]
struct Cli {
    /// Environment to deploy to
    #[arg(long, add = ArgValueCandidates::new(env_candidates))]
    env: String,

    /// Config file
    #[arg(long, add = ArgValueCompleter::new(PathCompleter::file()))]
    config: Option<std::path::PathBuf>,
}

fn env_candidates() -> Vec<CompletionCandidate> {
    // Read a local cache only. Never prompt, print, or block here.
    load_cached_envs()
        .unwrap_or_default()
        .into_iter()
        .map(|e| CompletionCandidate::new(e.name).help(Some(e.region.into())))
        .collect()
}

fn main() {
    // Must be the first line, before logging, config loading or network setup
    CompleteEnv::with_factory(Cli::command).complete();
    let cli = Cli::parse();
    // ...
}
```

- **Enum values:** if an argument's type derives `ValueEnum`, it already completes. You don't need a hook for it.
- **Fixed candidate list:** use `ArgValueCandidates` when the list doesn't depend on what the user has typed so far.
- **Depends on the typed prefix:** use `ArgValueCompleter`, which receives the current text as `&OsStr`. Use it for paths, remote IDs filtered by prefix, and similar cases.
- **Help text:** `.help(...)` adds a description to each candidate in shells that can show one (zsh and fish).

## 2. Keep the hook fast and pure

The shell runs your binary on **every Tab press**, so treat it as a hot path:

- **Call `CompleteEnv::complete()` first.** Anything that runs before it slows down every completion.
- **Print only candidates to stdout.** No prompts, no log lines, no file writes.
- **Time-box and cache network lookups.** Return an empty list on any failure. A slow or erroring Tab is worse than no suggestions.
- **Fill the cache from normal commands.** For example, `mytool env list` can refresh `~/.cache/mytool/envs.json` as a side effect. The completion hook then only reads the cache, which keeps it free of writes and still makes it instant.

## 3. Document the setup line for each shell

Your binary emits a small registration stub that calls back into itself. Because the stub doesn't contain the command tree, it can't go out of date when you add flags.

```sh
# bash (~/.bashrc)
source <(COMPLETE=bash mytool)
# zsh (~/.zshrc, after compinit)
source <(COMPLETE=zsh mytool)
# fish (~/.config/fish/config.fish)
COMPLETE=fish mytool | source
# PowerShell ($PROFILE)
$env:COMPLETE = "powershell"; mytool | Out-String | Invoke-Expression
```

In your README or install output, show users the line to add. Don't edit their rc files silently.

## 4. If you can't accept the unstable feature

Ship a stable static subcommand instead, and accept that values won't complete dynamically:

```rust
#[derive(clap::Subcommand)]
enum Commands {
    /// Print a shell completion script to stdout
    Completion { shell: clap_complete::Shell },
    // ...
}

// in main:
Commands::Completion { shell } => {
    clap_complete::generate(shell, &mut Cli::command(), "mytool", &mut std::io::stdout());
}
```

`mytool completion <bash|zsh|fish|powershell>` should only print the script to stdout. Packagers can run it in release CI and install the output to these locations:

| Shell | Install path |
|---|---|
| bash | `~/.local/share/bash-completion/completions/mytool` |
| zsh | `_mytool` in a directory on `$fpath`, before `compinit` runs |
| fish | `~/.config/fish/completions/mytool.fish` |

`#[arg(value_hint = ValueHint::FilePath)]` and similar hints still give static scripts path completion.

Pick one approach and document only that one. If you ship a static script and also document the dynamic one, users who install the static file won't get value completion and won't know why.

## 5. Test it

- Unit-test your candidate functions directly: empty cache, corrupt cache, and filtering by prefix.
- Add `Cli::command().debug_assert()` in a test to catch clap configuration errors.
- Manually check one smoke case per shell you support before each release. Nobody tests completions in CI until they break.
