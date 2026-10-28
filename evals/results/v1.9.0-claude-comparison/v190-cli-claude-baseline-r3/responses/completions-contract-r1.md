For Rust with clap, use **`clap_complete`**. It gives you two approaches. If you need dynamic value completion, use the second one.

## Option 1: Static scripts (simple, no dynamic values)

Add a hidden subcommand that prints the script:

```rust
use clap::{CommandFactory, Parser, Subcommand};
use clap_complete::{generate, Shell};

#[derive(Subcommand)]
enum Cmd {
    /// Print shell completions
    Completions { shell: Shell },
    // ...
}

// in main:
Cmd::Completions { shell } => {
    generate(shell, &mut Cli::command(), "mycli", &mut std::io::stdout());
}
```

These scripts only know what clap knows when the script is generated: subcommands, flags, `PossibleValue`s/`ValueEnum`, and `ValueHint`s such as `FilePath`, `DirPath` and `Hostname`. They can't run your code, so they can't list things like "branches in this repo" or "profiles from the config file."

## Option 2: Dynamic completions with `CompleteEnv` (recommended)

With this approach the shell calls your binary on every Tab press, so your Rust code decides the candidates:

```toml
clap_complete = { version = "4", features = ["unstable-dynamic"] }
```

```rust
use clap::{CommandFactory, Parser};
use clap_complete::engine::{ArgValueCompleter, CompletionCandidate};
use clap_complete::CompleteEnv;

#[derive(Parser)]
struct Cli {
    #[arg(long, add = ArgValueCompleter::new(complete_profile))]
    profile: Option<String>,
}

fn complete_profile(current: &std::ffi::OsStr) -> Vec<CompletionCandidate> {
    let prefix = current.to_string_lossy();
    load_profile_names()               // read config, query API, etc.
        .into_iter()
        .filter(|p| p.starts_with(&*prefix))
        .map(|p| CompletionCandidate::new(p).help(Some("profile".into())))
        .collect()
}

fn main() {
    CompleteEnv::with_factory(Cli::command).complete(); // must be first
    let cli = Cli::parse();
    // ...
}
```

If the candidate list doesn't depend on what the user has typed so far, `ArgValueCandidates::new(fn)` is simpler.

Users enable it once in their shell rc file:

```sh
# bash
source <(COMPLETE=bash mycli)
# zsh
source <(COMPLETE=zsh mycli)
# fish
COMPLETE=fish mycli | source
```

It also supports elvish and PowerShell.

**Gotchas:**
- **Run `CompleteEnv::complete()` before anything else.** That includes logging setup, config loading and network calls. When the `COMPLETE` env var is set, it prints the completions and exits.
- **Keep completers fast and side-effect free.** They run on every Tab press. Add a timeout or cache for anything slow, like network calls.
- **Check whether the feature is still marked unstable** in the `clap_complete` version you use. While it's unstable, the API can change in minor releases, so pin the version.
- **The completions always match the installed binary,** because the shell asks the binary itself. That's a real advantage over shipping script files that can go stale.

## Distribution

- **Homebrew:** `generate_completions_from_executable(bin/"mycli", shell_parameter_format: :clap)` handles the `COMPLETE=<shell>` convention, or you can point it at your `completions` subcommand.
- **Tarballs and distro packages:** generate the scripts in CI (or an `xtask`) by running the built binary, and install them to the standard locations:
  - bash: `share/bash-completion/completions/mycli`
  - zsh: `share/zsh/site-functions/_mycli`
  - fish: `share/fish/vendor_completions.d/mycli.fish`

  With dynamic mode, these files are just the small registration stubs, which is fine.
- **Avoid generating scripts in `build.rs`.** The output lands in `OUT_DIR`, which is hard for packagers to find. Generating from the built binary in CI is simpler.
- **Document the one-liners above in your README.** Many users install with `cargo install` and never get packaged completion files.

**Recommendation:** use `CompleteEnv` plus `ArgValueCompleter` for anything dynamic, and use `ValueEnum`/`ValueHint` for everything else, since those also work in dynamic mode. Then add the per-shell install lines to your README and package recipes.
