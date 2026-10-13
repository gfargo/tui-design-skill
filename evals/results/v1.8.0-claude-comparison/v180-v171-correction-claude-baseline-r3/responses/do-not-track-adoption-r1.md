**Short answer:** Not quite. Each of those three tools uses its own variable. `DO_NOT_TRACK` is a community proposal ([consoledonottrack.com](https://consoledonottrack.com)), not an established standard. You should support both: your own variable and `DO_NOT_TRACK`.

**What those tools use:**
- **Homebrew:** `HOMEBREW_NO_ANALYTICS=1` (or `brew analytics off`)
- **Gatsby:** `GATSBY_TELEMETRY_DISABLED=1` (or `gatsby telemetry --disable`)
- **.NET SDK:** `DOTNET_CLI_TELEMETRY_OPTOUT=1`

I'm not sure whether any of them also check `DO_NOT_TRACK` today. Support has been requested in several projects and added in some. Check their current docs before you cite them as examples. Either way, the tool-specific variable is the main mechanism in all three.

**Your telemetry is opt-in, which changes things:** if it's off by default, a user who never opted in has nothing to opt out of. An opt-out variable still helps in a few cases:

1. **Hard override.** If `DO_NOT_TRACK=1` or your own `YOURTOOL_TELEMETRY_DISABLED=1` is set, never send anything, even if a config file says the user opted in. This helps people who share dotfiles, use shared machines, or set policy in CI or corporate images.
2. **Clear precedence.** For example: the env var disables telemetry → explicit config opt-in enables it → the default is off.
3. **Truthy parsing.** Treat any non-empty value except `0` or `false` as "disabled". People write `DO_NOT_TRACK=true`, `=yes` and `=1`.

**Suggested setup:**
- Opt in with something like `yourtool telemetry enable`, which writes to the config file.
- Honor `DO_NOT_TRACK` (costs almost nothing and respects users who set it globally).
- Honor `YOURTOOL_TELEMETRY_DISABLED` (easy to find, and matches what people expect from Homebrew, Gatsby and .NET).
- Show the current state in `yourtool telemetry status`, and document exactly what gets collected.
