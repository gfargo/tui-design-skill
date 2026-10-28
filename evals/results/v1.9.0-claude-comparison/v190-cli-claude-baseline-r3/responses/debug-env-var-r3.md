Yes, but not on its own. Use a namespaced variable and a flag as the main switches, and treat `DEBUG` as an extra trigger only when it names your tool.

**Why plain `DEBUG` is risky:**
- **It's already in use.** In the Node world, the `debug` package reads `DEBUG` as a list of name patterns (`DEBUG=express:*`, `DEBUG=*`). Lots of tools and CI setups set it, so someone debugging a different tool would suddenly get your stack traces too.
- **Its meaning is unclear.** Some people use `DEBUG=1`, some `DEBUG=true`, some `DEBUG=myapp:*`. If you turn on for any non-empty value, even `DEBUG=0` enables stack traces.
- **Your own dependencies may read it.** If any of them use `debug`, `DEBUG=*` floods the output with their logs too.

**What I'd do:**

1. **Flag first:** `--debug` (or `--verbose` / `-v`). Users can find it in `--help`, and it applies to one command at a time.
2. **Namespaced env var:** `MYCLI_DEBUG=1`, for setting it across a whole shell session or CI job. Treat only `1`, `true` and `yes` as on.
3. **Optionally honor `DEBUG`, but only when it names your tool.** Turn on if it matches `mycli`, `mycli:*` or `*`. That follows the `debug` convention instead of clashing with it, and Node users will try it by instinct.

```js
const debugEnabled =
  argv.debug ||
  /^(1|true|yes)$/i.test(process.env.MYCLI_DEBUG ?? '') ||
  (process.env.DEBUG ?? '').split(/[\s,]+/).some(p => p === '*' || p === 'mycli' || p.startsWith('mycli:'));
```

**Related practices:**
- By default, show a short, readable error message plus a hint: `Run with --debug for the full stack trace.`
- Write stack traces to **stderr**, never stdout, so they don't break piped output.
- In debug mode, include the error's underlying cause chain (`err.cause`), not just the top-level error.
- Precedence: a command-line flag should beat env vars. A `--no-debug` flag is useful if people set the env var globally.

If you tell me the language and argument parser you're using, I can adapt this to fit.
