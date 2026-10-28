**I'd avoid plain `DEBUG` as the main switch. Use a prefixed variable plus a flag instead.**

**Why not `DEBUG`:**
- **Name collision.** The npm `debug` package and many other tools already use `DEBUG`, often as `DEBUG=*` or `DEBUG=express:*`. Someone debugging a different tool in the same shell would suddenly get stack traces from yours.
- **Unclear values.** Is `DEBUG=0` on or off? What about `DEBUG=false`? Different tools answer differently, so people can't predict what yours will do.
- **It leaks into child processes.** If your CLI starts other programs, they may react to it too.

**What I'd do instead:**
1. **Add a `--debug` (or `--verbose`) flag** as the main way to turn it on. Users can find it in `--help`, and it applies to a single run.
2. **Add a prefixed variable like `MYCLI_DEBUG=1`** for cases where a flag is awkward, such as CI, wrappers or aliases. Treat it as on only for clear values like `1`, `true` or `yes`. Treat empty, `0` and `false` as off.
3. **Precedence:** the flag beats the env var, which beats the default.
4. **Optional:** to work alongside the `debug` convention, also honor `DEBUG` when it names your tool (`DEBUG=mycli` or `DEBUG=mycli:*`), but not a bare `DEBUG=1`. That's polite to users who expect it, and `DEBUG=*` still turns on everything, which is how that convention is supposed to work.

**Related tips:**
- Even without debug mode, print a short one-line error and a hint like `Run with --debug for a stack trace`.
- Print stack traces to stderr, never stdout, so piped output stays clean.
- If you also have `NO_COLOR`/`--quiet`-style settings, give them the same flag-plus-prefixed-variable pattern so everything behaves alike.

If you tell me the language or framework, I can show how it usually wires this up (e.g. Click, Cobra, clap or oclif).
