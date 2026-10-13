No. None of those three use `DO_NOT_TRACK`. Each one turned it down and kept its own variable:

| Tool | Opt-out variable |
|---|---|
| Homebrew | `HOMEBREW_NO_ANALYTICS=1` |
| Gatsby | `GATSBY_TELEMETRY_DISABLED=1` |
| .NET SDK | `DOTNET_CLI_TELEMETRY_OPTOUT=1` |

`DO_NOT_TRACK=1` is a proposed convention that few tools have adopted. netdata, tilt and the GitHub CLI support it. Even gh has its own `GH_TELEMETRY` variable, and that variable overrides `DO_NOT_TRACK`.

**My recommendation: define your own and also honor `DO_NOT_TRACK`.**

- **Your own controls:** an env var such as `MYTOOL_TELEMETRY=0|1`, plus a subcommand or config key like `mytool telemetry enable|disable|status`. Users and docs will look for these first.
- **Honor `DO_NOT_TRACK=1` too.** It's a single env lookup, and it helps people who set it everywhere.
- **Let opt-out win.** Since your telemetry is opt-in, `DO_NOT_TRACK=1` or your own disable setting should still turn it off if the user opted in earlier, for example in a shared dotfile or a container image. Check the opt-out first and treat it as an absolute veto. The Netlify CLI was once caught sending an event to report that the user had disabled telemetry.
- **Turn it off in CI** automatically (`CI` env var is set).
- **Show what you collect** when someone opts in, before any data is sent. `telemetry status` should show the current state and which setting decided it.

Rough order for deciding whether to send anything:

```
if DO_NOT_TRACK=1 or MYTOOL_TELEMETRY=0 or CI → off
else if MYTOOL_TELEMETRY=1 or config.telemetry=true → on
else → off (opt-in default)
```

Source: the skill's `references/cli-basics.md:474-478`.
