**No. Use a `--debug` flag, plus an environment variable with your tool's prefix, such as `MYTOOL_DEBUG=1`.**

**Why not plain `DEBUG`:**
- **Another tool already owns it.** In the Node world, the widely used `debug` package reads `DEBUG` as a list of name patterns, like `DEBUG=express:*` or `DEBUG=*`. People often leave `DEBUG=*` set in their shell or CI to debug some other program. If your tool reads it too, users get stack traces they never asked for.
- **The values don't match.** `debug` expects patterns like `*`, while your tool would expect something like `DEBUG=1`. Whatever you pick will clash with how some users have already set it. And if your tool runs on Node, `DEBUG=*` also turns on logging from every dependency that uses `debug`, so the two outputs mix.
- **It's not clear who it's for.** A prefixed name says exactly which tool it controls and won't affect child processes or wrapper scripts that pass the environment along.

**What to do instead:**
- **Hide stack traces by default.** Catch expected errors and print a short rewritten message to stderr that starts with `error:`. Put the fix command (or a docs link) on the last line.
- **Show the full trace only with `--debug` or `MYTOOL_DEBUG=1`.** Send it to stderr, never stdout, so piped output stays clean.
- **Keep it separate from `-v`/`-vv`.** Verbose flags make normal output more detailed. `--debug` adds internal details like traces, timings and the parsed config.
- **Let the flag win over the environment variable.** A flag typed on the command line should override a variable set in the shell.
- **Mention it in the error message for unexpected failures.** For example: `error: unexpected failure (run with --debug for details)`. That way users don't need to know the variable exists before they need it.
- **If your tool has a full-screen interface,** never print traces onto the screen it controls. Write them to a log file or show them after the terminal is restored.

One caveat: Bubble Tea's own example gates logging to a file with `DEBUG`, and the skill's Go reference repeats that example. That's fine for a local development setup you control. For a variable that ships to users, use the prefixed name.
