Use **`clap` as the single command definition, `clap_complete` for generated scripts, and runtime completion hooks for values that change**.

Treat completion as a small, noninteractive CLI protocol: scripts and candidates go to stdout; no prompts, progress bars, or update notices.

1. **Generate static completions from your parser.**

   Expose:

   ```text
   mytool completion <bash|zsh|fish|pwsh>
   ```

   The command should print the script without installing anything. Its implementation is essentially:

   ```rust
   use clap::CommandFactory;
   use clap_complete::{generate, Shell};

   fn print_completion(shell: Shell) {
       generate(
           shell,
           &mut Cli::command(),
           "mytool",
           &mut std::io::stdout(),
       );
   }
   ```

   Map your public `pwsh` spelling to `Shell::PowerShell`; clap_complete’s shell enum uses `powershell`.

   Define fixed choices using `ValueEnum` or possible values, and annotate paths with `ValueHint::FilePath` or `DirPath`. This gives the generator useful information without custom shell code.

2. **Use runtime hooks for changing argument values.**

   Branch names, profiles, environments, and remote resource names need a lookup when the user presses Tab. **Static `generate()` scripts do not automatically invoke custom Rust value completers.**

   `clap_complete` provides this through its **`unstable-dynamic`** feature:

   ```toml
   [dependencies]
   clap = { version = "4", features = ["derive"] }
   clap_complete = { version = "4", features = ["unstable-dynamic"] }
   ```

   A minimal integration looks like:

   ```rust
   use std::ffi::OsStr;
   use clap::{CommandFactory, Parser};
   use clap_complete::{
       CompleteEnv,
       engine::{ArgValueCompleter, CompletionCandidate},
   };

   #[derive(Parser)]
   #[command(name = "mytool")]
   struct Cli {
       #[arg(long, add = ArgValueCompleter::new(complete_profile))]
       profile: Option<String>,
   }

   fn complete_profile(current: &OsStr) -> Vec<CompletionCandidate> {
       let Some(prefix) = current.to_str() else {
           return Vec::new();
       };

       // Replace with a fast, read-only local configuration lookup.
       ["development", "staging", "production"]
           .into_iter()
           .filter(|name| name.starts_with(prefix))
           .map(CompletionCandidate::new)
           .collect()
   }

   fn main() {
       // Handle completion before parsing or ordinary application startup.
       CompleteEnv::with_factory(Cli::command).complete();

       let cli = Cli::parse();
       // Run the application.
   }
   ```

   For example, dynamic Bash registration uses:

   ```bash
   source <(COMPLETE=bash mytool)
   ```

   This registration path is distinct from static script generation. Document which mode users should enable, and verify dynamic shell support against your pinned crate version. The dynamic API remains unstable; keep `Cargo.lock` committed and review upgrades.

3. **Ship scripts with releases and packages.**

   Generate them during release packaging from the same command tree as the binary. Document manual installation:

   | Shell | Installation |
   |---|---|
   | Bash | `~/.local/share/bash-completion/completions/mytool`, with bash-completion enabled |
   | Zsh | `_mytool` in a directory on `$fpath`, configured before `compinit` |
   | Fish | `~/.config/fish/completions/mytool.fish` |
   | PowerShell | Save the script and dot-source it from `$PROFILE` |

   Have package managers install the appropriate files. Show manual setup instructions; never silently edit shell startup files.

4. **Keep every Tab press cheap and harmless.**

   Aim for under 100 ms. Prefer local state or an existing cache; bound remote requests with short timeouts and return no candidates on failure. Completion must never trigger authentication, mutate resources, or launch the normal command. Let the completion framework handle shell escaping.

   Before shipping, test nested commands, `--flag=value`, spaces and Unicode, empty prefixes, missing credentials, and offline behavior. Check stdout purity and run a real completion smoke test in each advertised shell.

If you need stable APIs throughout, ship static `clap_complete` scripts plus narrowly scoped shell adapters calling a hidden, read-only candidate endpoint. That costs more maintenance, but avoids depending on the experimental dynamic API.