No. Those three tools don't follow `DO_NOT_TRACK`. Each one uses its own variable:

| Tool | Opt-out |
|---|---|
| Homebrew | `HOMEBREW_NO_ANALYTICS=1` |
| Gatsby | `GATSBY_TELEMETRY_DISABLED=1` |
| .NET SDK | `DOTNET_CLI_TELEMETRY_OPTOUT=1` |

`DO_NOT_TRACK=1` is a proposed convention that few tools have adopted. Netdata, Tilt and the GitHub CLI honor it, but the big tools you named chose their own variables.

**Define your own, and honor `DO_NOT_TRACK` too.**

- **Your own controls:** an environment variable like `MYTOOL_TELEMETRY=0|1` and a subcommand like `mytool telemetry enable|disable|status` that writes to your config file. gh works this way: it has a `GH_TELEMETRY` variable and a `telemetry` config key, and `GH_TELEMETRY` overrides `DO_NOT_TRACK`.
- **`DO_NOT_TRACK=1`:** respect it anyway. It costs one env lookup, and the people who set it care about privacy.
- **CI:** skip telemetry when `CI` is set.

**Because yours is opt-in:**

- **Default is off.** Send nothing until the user explicitly turns it on, through a prompt they answer yes to, the subcommand, or your variable.
- **A user who opts in still has a veto.** If someone opted in on their laptop but has `DO_NOT_TRACK=1` set in one shell, or runs your tool in CI, don't send anything. Check the "off" signals first and treat any one of them as final.
- **Never report the opt-out.** Netlify CLI once sent an event recording that the user had disabled telemetry. Don't send an "opted out" or "declined" ping.
- **Ask before the first event.** If you prompt, do it before anything is collected, only on an interactive TTY, and say what you collect and where the docs are. Homebrew shows its notice before sending anything. If there's no TTY, don't prompt; leave telemetry off.

A sketch of the order to check things in:

```
if DO_NOT_TRACK=1 or CI is set      -> off
elif MYTOOL_TELEMETRY is set        -> use it
elif config.telemetry is set        -> use it
else                                -> off  (opt-in default)
```

This comes from the telemetry section of the skill's `references/cli-basics.md:472`.
