Use **`clap` as your command schema and `clap_complete` for shell integration**. Ship static completions first, then add runtime completion for values such as project names, profiles, or resource IDs.

There are two distinct paths:

| Completion | Implementation |
|---|---|
| Commands, flags, fixed enums, file paths | Stable `clap_complete::generate()`, with Clap value parsers and `ValueHint` metadata |
| Values discovered at runtime | `clap_complete` dynamic completion, currently gated by `unstable-dynamic` |

**Expose a script-generation command:**

```text
mytool completion bash
mytool completion zsh
mytool completion fish
mytool completion pwsh
```

It should print only shell source to stdout and make no changes to the filesystem. Map your public `pwsh` spelling to `clap_complete::Shell::PowerShell`.

For static generation, the handler’s core is:

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

Generate scripts from the same command definition used for parsing. Declare fixed choices with `ValueEnum`, and annotate path arguments with `ValueHint::FilePath` or `DirPath`.

**For dynamic values, install the runtime hook before ordinary parsing or application startup.** The general integration is:

```rust
fn main() {
    clap_complete::CompleteEnv::with_factory(|| Cli::command())
        .complete();

    let cli = Cli::parse();
    // Normal command dispatch.
}
```

This requires `clap_complete`’s `unstable-dynamic` feature. Attach an `ArgValueCompleter` to arguments that need runtime candidates. The `COMPLETE=<shell>` protocol generates the shell integration and handles completion requests; use its generated integration when you need these callbacks. **Stable static `generate()` output does not automatically invoke dynamic callbacks.** Pin and test the chosen crate version because these APIs remain unstable.

Treat each completion invocation as a tiny, read-only query:

- Prefer local config, workspace metadata, and existing caches.
- Aim for under 100 ms; bound remote requests and return cached or empty results on failure.
- Never prompt, authenticate interactively, launch a TUI, or perform mutations.
- Suppress update notices, progress, and ordinary logs. Stdout belongs exclusively to the completion protocol.
- Let the shell adapter handle escaping; keep candidate values separate from descriptions.

**Ship the integration with your packages**, and document manual installation:

| Shell | Manual installation |
|---|---|
| Bash | `~/.local/share/bash-completion/completions/mytool`, with bash-completion installed |
| Zsh | `_mytool` in a directory on `$fpath`, configured before `compinit` |
| Fish | `~/.config/fish/completions/mytool.fish` |
| PowerShell | Save the generated `.ps1` and dot-source it from `$PROFILE` |

Never silently edit shell startup files. Include generation instructions for `cargo install` users, since installing the binary alone does not install shell integration.

Before release, test nested subcommands, `--flag=value`, spaces and Unicode, cursor-in-the-middle completion, offline failures, and clean protocol output. Run a smoke test in each supported shell, and check dynamic support individually rather than assuming it matches static generator support.

My recommendation: **ship stable static completions for every supported shell, and enable dynamic completion only for shells you have tested end to end.** If unstable dependencies are unacceptable, retain static generation and maintain small shell adapters around a private, read-only candidate endpoint.