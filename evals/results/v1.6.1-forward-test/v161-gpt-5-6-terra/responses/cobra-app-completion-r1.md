Users run:

```bash
shipctl completion bash
```

It prints the Bash completion script to stdout, so they can source or install it, e.g. `shipctl completion bash > /etc/bash_completion.d/shipctl`.

`cobra-cli` is the development-time scaffolding tool. Use `cobra-cli add completion` to add the `completion` subcommand to `shipctl`; it does not generate completions for `shipctl` when users run `cobra-cli completion bash`—that only completes `cobra-cli` itself.
