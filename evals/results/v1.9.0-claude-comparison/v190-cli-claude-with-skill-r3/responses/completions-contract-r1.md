**Recommendation:** use `clap_complete`. Offer a `mytool completion <shell>` subcommand that prints the script to stdout. Give every argument the free static completions first: enums, file paths and subcommands. Add dynamic value completion only for values that live at runtime, like profiles, remote names or resource IDs. That goes through clap's `COMPLETE=<shell>` hook. The hook is still gated behind `clap_complete`'s `unstable-dynamic` feature, so pin the exact version.

## 1. Static completions (stable)

```toml
[dependencies]
clap = { version = "4", features = ["derive"] }
clap_complete = "4"
```

```rust
use clap::{CommandFactory, Parser, Subcommand, ValueHint};
use clap_complete::{generate, Shell};

#[derive(Parser)]
#[command(name = "mytool")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Push a directory to a bucket
    Push {
        #[arg(value_hint = ValueHint::DirPath)]
        src: std::path::PathBuf,
        #[arg(long, value_enum, default_value_t = Format::Text)]
        output: Format,          // completes text/json for free
    },
    /// Print a shell completion script to stdout
    Completion { shell: Shell }, // bash, zsh, fish, powershell, elvish
}

fn main() {
    let cli = Cli::parse();
    match cli.command {
        Commands::Completion { shell } => {
            generate(shell, &mut Cli::command(), "mytool", &mut std::io::stdout());
        }
        // ...
    }
}
```

`ValueEnum` types and `value_hint` already cover most arguments. You only need runtime lookups for the remaining ones.

## 2. Dynamic value completion (`unstable-dynamic`)

```toml
clap_complete = { version = "=4.5.X", features = ["unstable-dynamic"] }  # pin exactly; the API can change between releases
```

```rust
use clap_complete::engine::{ArgValueCompleter, CompletionCandidate};
use clap_complete::CompleteEnv;

#[derive(Subcommand)]
enum Commands {
    Deploy {
        #[arg(long, add = ArgValueCompleter::new(complete_profile))]
        profile: String,
    },
    // ...
}

fn complete_profile(current: &std::ffi::OsStr) -> Vec<CompletionCandidate> {
    let Some(prefix) = current.to_str() else { return vec![] };
    load_profiles_from_config()          // local, fast, no network
        .unwrap_or_default()             // failure = no candidates, never an error
        .into_iter()
        .filter(|p| p.name.starts_with(prefix))
        .map(|p| CompletionCandidate::new(p.name).help(Some(p.region.into())))
        .collect()
}

fn main() {
    // Must run FIRST: before logging init, config prompts, update checks, anything that prints.
    CompleteEnv::with_factory(Cli::command).complete();
    let cli = Cli::parse();
    // ...
}
```

Users register it once, and the shell then calls your binary on every Tab press:

```sh
# bash (~/.bashrc)
source <(COMPLETE=bash mytool)
# zsh (~/.zshrc)
source <(COMPLETE=zsh mytool)
# fish (~/.config/fish/config.fish)
COMPLETE=fish mytool | source
```

Once you adopt the dynamic engine, have `mytool completion <shell>` print that same registration script. That way there's one install story, and the static and dynamic paths don't drift apart.

## 3. Rules for the completion hook

Your binary now runs on every keystroke-driven Tab, so:

- **Fast:** aim for well under ~100 ms. Read local config or cache files. Don't open DB connections or run heavy startup work.
- **Pure:** no prompts, no file writes, no telemetry, no update checks. Stdout carries candidates only, and stderr stays silent too, because stray output corrupts the prompt.
- **Network values** (like `kubectl` resource names or `gh` PRs): time-box the lookup, serve from a short-TTL cache, and return an empty list when it fails or times out. A completion that hangs for 5 seconds is worse than none.
- **Filter by `current`** yourself, and attach `.help(...)` descriptions. zsh and fish show them next to each candidate.

## 4. Shipping it

- **Contract:** `mytool completion <bash|zsh|fish|powershell>` prints to stdout, exits 0 and touches nothing else.
- **Document install locations:**
  - bash: `~/.local/share/bash-completion/completions/mytool`
  - zsh: a file named `_mytool` in a directory on `$fpath`, before `compinit` runs
  - fish: `~/.config/fish/completions/mytool.fish`
- **Packages:** in release CI, run the built binary for each shell and put the output files in the tarball, deb or rpm. A Homebrew formula can call `generate_completions_from_executable(bin/"mytool", "completion")`.
- **Never edit rc files silently.** Print the line and tell the user where to add it, the way starship, zoxide and mise do.
- **Man pages:** generate them from the same command tree with `clap_mangen`, so help, completions and docs stay in sync.

## 5. Testing

- Unit-test each completer function: prefix filtering, empty config, unreadable config (should return `[]`) and non-UTF-8 input.
- Golden-test `mytool completion <shell>` output per shell, so a clap upgrade that changes the scripts shows up in review.
- Do one manual or PTY smoke test per shell after bumping the pinned `clap_complete` version. That's where the unstable API can break.

**When to skip dynamic completion:** if every value can be expressed as a `ValueEnum` or `ValueHint`, stay on the stable `generate()` path and skip the unstable feature entirely.
