Use **`clap` + `clap_complete`**, with static completions as your baseline and runtime hooks for values such as project names, branches, or remote resources.

1. **Generate from your command definition.** Keep flags, subcommands, help, and completions in the same clap command tree. Declare fixed choices with `ValueEnum` or a value parser, and annotate paths with `ValueHint`.

   Expose:

   ```text
   mytool completion <bash|zsh|fish|powershell>
   ```

   It should print shell source to stdout, exit successfully, and make no filesystem changes. The stable generation API is:

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

   Clap’s shell spelling is `powershell`; optionally accept `pwsh` as an alias.

2. **Use runtime completion for changing argument values.** Static `generate()` scripts don’t automatically call your application to discover live values. `clap_complete` provides runtime completion through its **`unstable-dynamic`** feature, using `CompleteEnv` and argument completers such as `ArgValueCompleter`.

   The integration starts before normal argument parsing or application initialization:

   ```rust
   fn main() {
       clap_complete::CompleteEnv::with_factory(Cli::command)
           .complete();

       let cli = Cli::parse();
       // Normal command execution.
   }
   ```

   Attach a completer to each relevant argument; have it return candidates from local configuration, cached data, or a bounded lookup. The runtime mechanism uses `COMPLETE=<shell>` for registration and completion requests. **Install its generated registration script when you want dynamic values**—a static script alone won’t enable those hooks.

   Because this API is feature-gated and unstable, pin and test your dependency version, and verify dynamic support for each shell you promise. If that instability is unacceptable, keep static generation and ship shell-specific adapters calling a hidden completion endpoint.

3. **Make every Tab request cheap and quiet.**

   - Aim for under 100 ms, including process startup.
   - Return only the framework’s candidate protocol on stdout.
   - Never prompt, launch authentication, show progress, or check for updates.
   - Keep completion read-only; refresh caches during ordinary commands or an explicit refresh.
   - Time-box network requests; use cached results or return no candidates on failure.
   - Let the shell integration handle quoting. Test spaces, quotes, Unicode, and values beginning with `-`.

4. **Ship scripts with releases and packages.** Generate them from the matching release’s command tree. Let package managers install them into their completion directories, and document manual installation:

   | Shell | User installation |
   |---|---|
   | Bash | `~/.local/share/bash-completion/completions/mytool`, with bash-completion enabled |
   | Zsh | `_mytool` in a directory on `$fpath`, configured before `compinit` |
   | Fish | `~/.config/fish/completions/mytool.fish` |
   | PowerShell | A script explicitly sourced from `$PROFILE` |

   Show any required profile lines; don’t silently edit users’ shell configuration.

Before release, test both generated scripts and actual Tab behavior: flags, nested subcommands, fixed choices, dynamic values, `--option=value`, quoting, missing credentials, and offline operation. Use black-box tests for candidate output and a small shell integration smoke test for each supported shell.