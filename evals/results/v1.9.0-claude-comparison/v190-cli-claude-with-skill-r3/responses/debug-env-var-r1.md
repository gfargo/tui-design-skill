**No. Use a `--debug` flag, and a variable namespaced to your tool, such as `MYTOOL_DEBUG=1`, for cases where you can't change the command line.**

A plain `DEBUG` variable is already taken. Node's `debug` package uses it, and many tools read it.
- **It turns on by accident.** Someone who set `DEBUG=*` to debug some other tool, or left it in their shell, would suddenly get stack traces from your CLI. In scripts and CI that's noise on stderr they didn't ask for.
- **It doesn't mean the same thing everywhere.** `DEBUG=1` is the obvious value for your tool, but it matches nothing in `debug`'s pattern syntax. People who use both will be confused either way.

A good setup:

1. **No stack traces by default.** Catch expected errors and print a plain message starting with `error:`. Put the fix (a command or a docs link) on the last line, because that's where the eye lands.
2. **Show traces with `--debug` or `MYTOOL_DEBUG=1`.** The flag is easy to find in `--help`. The variable covers wrappers, CI, and cases where you can't edit the call.
3. **Keep it separate from verbosity.** `-v`/`-vv` make output chattier. `--debug` adds traces and internals. Errors still print under `-q`.
4. **Send traces to stderr**, never stdout, so piped output isn't corrupted. If it's a full-screen TUI, write debug output to a log file, because anything printed to the screen the TUI owns gets swallowed or breaks the frame.

```
$ mytool sync
error: could not reach api.example.com (connection refused)
Check your network or set MYTOOL_API_URL. Run with --debug for details.
```

One thing to fix in the skill itself: `references/ecosystem-go.md:543` gates Bubble Tea file logging on `os.Getenv("DEBUG")`, while `references/cli-basics.md:106` says not to read plain `DEBUG`. The Go example should probably use a namespaced variable so the two references agree.
