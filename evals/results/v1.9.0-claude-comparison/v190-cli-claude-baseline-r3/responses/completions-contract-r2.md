This assumes you're using **clap**, which most Rust CLIs do. I haven't looked at your project; the working directory looks empty, so this is general guidance. My recommendation is to use clap_complete's **dynamic completion engine** (`CompleteEnv`) for everything. Use the static generator only if you can't accept an unstable API.

## Option A (recommended): dynamic completions via `CompleteEnv`

With this approach, the shell calls your binary on every Tab press, so your Rust code decides the candidates. That covers things like profile names from a config file, branch names, or remote resources.

```toml
# Cargo.toml
[dependencies]
clap = { version = "4", features = ["derive"] }
clap_complete = { version = "4.5", features = ["unstable-dynamic"] }
```

```rust
use std::ffi::OsStr;
use clap::{CommandFactory, Parser};
use clap_complete::engine::{ArgValueCompleter, CompletionCandidate};
use clap_complete::env::CompleteEnv;

#[derive(Parser)]
struct Cli {
    /// Fully dynamic: computed at Tab time
    #[arg(long, add = ArgValueCompleter::new(complete_profile))]
    profile: Option<String>,

    /// Static hints still work for free
    #[arg(long, value_hint = clap::ValueHint::FilePath)]
    config: Option<std::path::PathBuf>,
}

fn complete_profile(current: &OsStr) -> Vec<CompletionCandidate> {
    let Some(prefix) = current.to_str() else { return vec![] };
    load_profiles() // your fn; must be fast and must not panic
        .unwrap_or_default()
        .into_iter()
        .filter(|p| p.starts_with(prefix))
        .map(CompletionCandidate::new) // .help(Some("desc".into())) for descriptions
        .collect()
}

fn main() {
    // Must run first, before logging setup, config loading, etc.
    CompleteEnv::with_factory(Cli::command).complete();

    let cli = Cli::parse();
    // ...
}
```

Users enable it with one line in their shell config:

```sh
# bash (~/.bashrc)
source <(COMPLETE=bash mycli)
# zsh (~/.zshrc)
source <(COMPLETE=zsh mycli)
# fish (~/.config/fish/config.fish)
COMPLETE=fish mycli | source
```

PowerShell and elvish are also supported.

**Things to know:**
- **It's still feature-gated as `unstable-dynamic`.** Pin the minor version and read the changelog when you upgrade.
- **Startup time is now completion latency.** Call `CompleteEnv` before any expensive setup. Keep completers cheap: avoid the network if you can, use short timeouts and a cache if you can't.
- **Completers should fail silently.** Return `vec![]` on errors. Never print to stdout or stderr from them, because the output corrupts the shell's completion.
- **`ArgValueCandidates`** is a simpler variant for when the candidate list doesn't depend on what the user has typed so far.
- `ValueEnum` and `value_parser(["a", "b"])` values get completed automatically, with no extra code.

## Option B: static scripts via `clap_complete::generate`

This works if you only need flags, subcommands, enums and file paths. It's stable and has no runtime cost. Expose it as a hidden subcommand rather than generating it in `build.rs`, because `OUT_DIR` output is awkward for packagers to find:

```rust
#[derive(clap::Subcommand)]
enum Cmd {
    #[command(hide = true)]
    Completions { shell: clap_complete::Shell },
    // ...
}

// in main:
Cmd::Completions { shell } => {
    clap_complete::generate(shell, &mut Cli::command(), "mycli", &mut std::io::stdout());
}
```

To get dynamic values in this mode, you'd have to hand-write shell functions that call something like `mycli __list-profiles`, separately for each shell. Option A exists to avoid exactly that.

## Shipping it

- **Release tarballs:** in CI, run the binary to generate the per-shell files and include them in a `completions/` directory, plus man pages via `clap_mangen` while you're at it. For Option A, the generated file is just the small registration stub. Generate it with the installed binary name, since the stub calls your binary by name or path.
- **Standard install locations:**
  - bash: `/usr/share/bash-completion/completions/mycli`
  - zsh: `/usr/share/zsh/site-functions/_mycli`
  - fish: `/usr/share/fish/vendor_completions.d/mycli.fish`
- **Homebrew:** use `generate_completions_from_executable(bin/"mycli", "completions")` for Option B. For Option A, use `bash_completion.install`, `zsh_completion.install` and `fish_completion.install` with the pre-generated files.
- **`cargo install` users:** document the one-line `source <(COMPLETE=… mycli)` setup in your README, since cargo doesn't install completion files.

If you share your CLI's structure, or the values you want completed dynamically, I can sketch the actual completers.
