**Short version:** use `clap_complete`. If you only need flags, subcommands, and fixed value sets, generate static scripts behind a `completion <shell>` subcommand. If you need runtime values (profiles, branches, remote resources), use `CompleteEnv` (`COMPLETE=<shell>`). It's still behind `clap_complete`'s `unstable-dynamic` feature, so pin the version exactly. Keep the `completion` subcommand either way, because packagers and docs rely on it.

## 1. The contract to ship

- `mytool completion <bash|zsh|fish|powershell>` prints the script to **stdout** and does nothing else: no prompts, no file writes.
- Document where each shell loads it from:
  - bash: `~/.local/share/bash-completion/completions/mytool`
  - zsh: a file named `_mytool` in a directory on `$fpath`, set up before `compinit`
  - fish: `~/.config/fish/completions/mytool.fish`
- Never edit the user's rc files yourself. Print the line for them to add.

## 2. Static completions (stable)

```toml
[dependencies]
clap = { version = "4", features = ["derive"] }
clap_complete = "4"
```

```rust
use clap::{CommandFactory, Parser, Subcommand, ValueEnum};
use clap_complete::{generate, Shell};

#[derive(Parser)]
#[command(name = "mytool")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Print a shell completion script to stdout
    Completion { shell: Shell },
    Deploy {
        #[arg(long, value_enum)]
        env: Env, // fixed sets complete for free via ValueEnum
        #[arg(value_hint = clap::ValueHint::FilePath)]
        manifest: std::path::PathBuf, // hints map to the shell's file completion
    },
}

#[derive(Clone, ValueEnum)]
enum Env { Dev, Staging, Prod }

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Completion { shell } => {
            let mut cmd = Cli::command();
            let name = cmd.get_name().to_string();
            generate(shell, &mut cmd, name, &mut std::io::stdout());
        }
        Cmd::Deploy { .. } => { /* ... */ }
    }
}
```

`ValueEnum` and `value_hint` cover more cases than people expect. Use them before reaching for dynamic completion.

## 3. Dynamic argument values (`unstable-dynamic`)

```toml
clap_complete = { version = "=4.5.x", features = ["unstable-dynamic"] }  # pin exactly; the API can change
```

```rust
use clap_complete::engine::{ArgValueCompleter, CompletionCandidate};
use clap_complete::CompleteEnv;

#[derive(Subcommand)]
enum Cmd {
    Use {
        #[arg(add = ArgValueCompleter::new(complete_profile))]
        profile: String,
    },
    // ...
}

fn complete_profile(current: &std::ffi::OsStr) -> Vec<CompletionCandidate> {
    let Some(prefix) = current.to_str() else { return vec![] };
    load_profile_names() // read local config/cache only, never block
        .unwrap_or_default() // on failure: no candidates, no error text
        .into_iter()
        .filter(|n| n.starts_with(prefix))
        .map(CompletionCandidate::new)
        .collect()
}

fn main() {
    // Must run before parse(). When COMPLETE is set, it answers the shell and exits.
    CompleteEnv::with_factory(Cli::command).complete();
    let cli = Cli::parse();
    // ...
}
```

Users register it once:

```sh
# bash / zsh
source <(COMPLETE=bash mytool)     # or COMPLETE=zsh
# fish
COMPLETE=fish mytool | source
```

How it works: the registered script is a small shim that runs your binary again on every Tab press. That shapes the rules for completers:

- **Fast and pure.** Print nothing on stdout except candidates. No prompts, logging, or writes. Set up `CompleteEnv` before any logging or tracing init so nothing gets printed during completion.
- **Time-box and cache network lookups.** A Tab that hangs for 2s feels broken. Read from a local cache, or refresh it in the background on normal runs. On a timeout or error, return an empty list.
- **Filter by prefix yourself.** Add `.help(Some("…".into()))` to candidates; zsh and fish show the description.

## 4. Keeping `completion <shell>` once you go dynamic

A static `generate()` script doesn't know about your custom completers. So once you adopt `CompleteEnv`, make `mytool completion <shell>` print the **dynamic shim**. The simplest way is to spawn your own binary with `COMPLETE=<shell>` set and pass its stdout through. Then the documented file locations and package-manager install steps keep working, and you have one mechanism instead of two that drift apart. Before you bake that output into a package, check that the shim calls `mytool` by name and not by a build-directory path.

## 5. Packaging

- **Release CI:** after building, run `mytool completion bash > completions/mytool.bash` (and the same for zsh and fish), then put the files in your tarballs, `.deb`/`.rpm`, and so on. This is simpler than generating them in `build.rs`, which forces you to share the CLI definition through `include!`.
- **Homebrew:** `generate_completions_from_executable(bin/"mytool", "completion")` calls exactly this subcommand.
- **cargo install users:** put the `source <(COMPLETE=… mytool)` lines in your README and in `mytool completion --help`.

## 6. Testing

- Call `Cli::command().debug_assert()` in a unit test to catch broken argument definitions.
- Unit-test completer functions directly: call them with a prefix, an empty prefix, non-UTF-8 input, and a missing or corrupt cache, and check the candidates you get back.
- Add one smoke test per shell: run `COMPLETE=bash mytool` (and the `completion` subcommand). Assert it exits 0, writes nothing to stderr, and prints a non-empty script.

The bottom line: use static generation if fixed values are enough, and switch to `CompleteEnv` when values depend on runtime state. In both cases, keep `completion <shell>` as the one documented entry point.
