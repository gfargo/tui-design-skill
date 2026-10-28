I'd use **`clap_complete`'s dynamic completion engine**. It handles both static structure (subcommands, flags) and runtime values from one mechanism, and the shell scripts can't drift out of sync with the binary. This assumes you're using clap. If you're not, that's the main reason to switch.

## 1. Pick an approach

| Approach | How it works | Dynamic values? |
|---|---|---|
| Static (`clap_complete::generate`) | You generate a full script per shell at build time or with a `completions` subcommand | No. Only `ValueEnum`, `PossibleValue` and `ValueHint` (file/dir hints) |
| Dynamic (`CompleteEnv`) | A small shell stub calls your binary back on every Tab | Yes, any Rust code |

## 2. Set up dynamic completion

```toml
# Cargo.toml
clap = { version = "4", features = ["derive"] }
clap_complete = { version = "4", features = ["unstable-dynamic"] }
```

```rust
use clap::{CommandFactory, Parser};
use clap_complete::engine::{ArgValueCompleter, CompletionCandidate};
use clap_complete::CompleteEnv;

#[derive(Parser)]
struct Cli {
    /// Profile to use
    #[arg(long, add = ArgValueCompleter::new(complete_profile))]
    profile: Option<String>,
}

fn complete_profile(current: &std::ffi::OsStr) -> Vec<CompletionCandidate> {
    let Some(prefix) = current.to_str() else { return vec![] };
    load_profile_names()                // your code: read config, list dir, etc.
        .unwrap_or_default()            // never error out during completion
        .into_iter()
        .filter(|p| p.starts_with(prefix))
        .map(|p| CompletionCandidate::new(p).help(Some("profile".into())))
        .collect()
}

fn main() {
    // Must run first. Exits early if invoked by the shell for completion.
    CompleteEnv::with_factory(Cli::command).complete();

    let cli = Cli::parse();
    // ... normal startup (logging, config, etc.)
}
```

Other useful parts of the engine:
- **`ArgValueCandidates::new(fn() -> Vec<CompletionCandidate>)`**: use this when you don't need the typed prefix and the shell does the filtering.
- **`PathCompleter`**: completes file paths, with filtering.
- **`CompletionCandidate`** also supports `.help()`, `.tag()` for grouping, and `.hide()`.

## 3. Ship it

**Users who install manually** add one line to their shell rc file:
```sh
source <(COMPLETE=bash mycli)    # ~/.bashrc
source <(COMPLETE=zsh mycli)     # ~/.zshrc
COMPLETE=fish mycli | source     # ~/.config/fish/config.fish
```
Elvish and PowerShell are supported too. Put these lines in your README and `--help` output.

**Package managers:** `COMPLETE=<shell> mycli` prints the registration stub, so packagers can write it to the standard locations:
- bash: `/usr/share/bash-completion/completions/mycli`
- zsh: `/usr/share/zsh/site-functions/_mycli`
- fish: `/usr/share/fish/vendor_completions.d/mycli.fish`

For `cargo-deb` or `cargo-generate-rpm`, generate these files in CI and list them as assets. For Homebrew, use `generate_completions_from_executable`. Recent Homebrew has a clap-style `shell_parameter_format: :clap` option that sets `COMPLETE=`, but check the current formula docs. Test each installed file in a clean shell, especially zsh's fpath-based loading.

## 4. Things to watch

- **Startup speed matters.** Your binary runs on every Tab press, so call `.complete()` before any expensive setup like tracing, config loading or network clients. Aim for under ~50 ms.
- **Fail silently.** Completers should return an empty list on errors, never panic, and never print to stdout. Anything written to stdout ends up in the user's command line.
- **Put timeouts on network lookups** and consider caching them, for example to a file in the cache dir with a TTL.
- **The feature is marked `unstable-dynamic`**, so the API can change in minor releases. Pin `clap_complete` to a minor version (`"=4.x"` or `~4.x`) and check the changelog when you upgrade. I can't verify whether it has been stabilized since my information was last updated, so check docs.rs.
- **Keep a static fallback if you need one.** If some users can't run the binary at completion time (locked-down environments, some distros' policies), you can also add a `mycli completions <shell>` subcommand using `clap_complete::generate`. Values will be static-only there.
- **Man pages:** `clap_mangen` fits the same build or CI step if you're already generating packaging artifacts.

If you share your CLI's structure, I can sketch completers for your specific arguments.
