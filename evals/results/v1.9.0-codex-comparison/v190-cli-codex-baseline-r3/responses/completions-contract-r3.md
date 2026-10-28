If you use `clap`, I’d ship **generated static completions as the baseline**, and add **runtime completion for values that depend on local or remote state**.

| What needs completing | Approach |
|---|---|
| Subcommands and flags | Generate from your `clap::Command` |
| Fixed choices, such as output formats | Declare a `ValueEnum` or possible values |
| Files and directories | Declare the appropriate `ValueHint` |
| Profiles, workspaces, branches, resource IDs | Query them at completion time |

**Static completions**

Use `clap_complete` and expose a command such as:

```text
mycli completions bash
mycli completions zsh
mycli completions fish
mycli completions powershell
```

Generate these from the same command definition used for parsing. Produce completion files during release packaging and install them through Homebrew, Debian/RPM packages, or your other installers. `cargo install` installs the executable; users generally need a documented extra step to install or activate completions.

Static generators handle syntax and declared choices, but they don’t automatically call your application to discover live values.

**Dynamic values**

`clap_complete` has an opt-in dynamic completion system, historically behind its `unstable-dynamic` feature. Its key APIs are `CompleteEnv` and `ArgValueCompleter`. The general structure is:

```rust
use clap::{CommandFactory, Parser};
use clap_complete::CompleteEnv;

fn main() {
    // Handle completion before normal argument parsing and application startup.
    CompleteEnv::with_factory(Cli::command).complete();

    let cli = Cli::parse();
    run(cli);
}
```

Attach an `ArgValueCompleter` to arguments whose candidates come from application state—for example, reading profile names from a configuration file. The shell integration invokes your binary when the user presses Tab.

Because this API has been evolving, pin a tested `clap_complete` version and check its feature names, callback signatures, and supported shells. Treat its dynamic integration as a separate backend from its static generators.

If you need a stable protocol or shells that the dynamic backend doesn’t support, ship small shell adapters calling a hidden endpoint such as:

```text
mycli __complete ...
```

Pass the full tokenized command line and cursor position so completion can handle partial input and dependencies such as `--project NAME --resource <TAB>`.

**Keep completion lightweight**

- Dispatch before authentication prompts, logging setup, update checks, or other startup work.
- Prefer local data and cached results; bound network requests with a short timeout.
- Return no candidates gracefully when offline or unauthenticated.
- Keep stdout exclusively for the completion protocol.
- Preserve spaces, Unicode, and shell quoting; avoid hand-building shell code.
- Test actual shell behavior, especially trailing spaces, `--flag=value`, paths, and incomplete arguments.

My default choice: **static files for packaged installation, plus `clap_complete`’s dynamic backend for live values where its shell support fits**. Use custom shell adapters only when you need additional compatibility or protocol control.

References: [clap_complete](https://docs.rs/clap_complete/latest/clap_complete/), [CompleteEnv](https://docs.rs/clap_complete/latest/clap_complete/env/struct.CompleteEnv.html), [ArgValueCompleter](https://docs.rs/clap_complete/latest/clap_complete/engine/struct.ArgValueCompleter.html).