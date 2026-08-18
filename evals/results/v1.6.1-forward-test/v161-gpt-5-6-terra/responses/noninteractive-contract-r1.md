No. `--no-input` is a useful, recognizable spelling, but it is not a universal CLI convention—and on its own it is underspecified.

Promise this contract instead:

> The command never prompts when its input channel is non-interactive. Every required value can be supplied through documented flags, environment variables, files, or stdin. If required information is missing, it fails before making changes, explains what is missing, and names the non-interactive way to provide it.

For an explicit override, support `--no-input` or, more clearly, `--non-interactive` as a convenience—but define it precisely:

- It disables all prompts and confirmation dialogs.
- It does not silently choose defaults for required or safety-sensitive inputs.
- Missing required input causes a usage-style failure (commonly exit 2) before side effects.
- Progress, logs, and prompts go to stderr; stdout remains result-only.
- It is separate from destructive confirmation: use `--yes` / `--force` for ordinary confirmations, and a typed flag such as `--confirm=RESOURCE` for severe actions.

A documentation-ready version:

```text
Automation behavior

When stdin is not a terminal, mycli does not prompt. Supply all required
values with flags, environment variables, input files, or stdin. If a required
value is absent, mycli exits before making changes and prints the flag or input
method needed.

Use --non-interactive (alias: --no-input) to enforce this behavior even in an
interactive terminal. This disables prompts; it never invents required values.
Use --yes to accept standard confirmation prompts.
```

Also make output automation-safe independently: offer structured output such as `--json`, disable animation outside a TTY, honor `NO_COLOR`, and keep diagnostics/progress on stderr.
