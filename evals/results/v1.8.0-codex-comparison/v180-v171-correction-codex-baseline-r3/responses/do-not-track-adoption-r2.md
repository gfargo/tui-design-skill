`DO_NOT_TRACK=1` is a **community proposal, not a universal standard followed by those three tools**. Their documented opt-outs are:

| Tool | Telemetry opt-out |
|---|---|
| [Homebrew](https://docs.brew.sh/Analytics) | `HOMEBREW_NO_ANALYTICS=1` or `brew analytics off` |
| [Gatsby](https://www.gatsbyjs.com/docs/telemetry/) | `GATSBY_TELEMETRY_DISABLED=1` or `gatsby telemetry --disable` |
| [.NET SDK](https://learn.microsoft.com/en-us/dotnet/core/tools/telemetry) | `DOTNET_CLI_TELEMETRY_OPTOUT=1` or `true` |

The [DO_NOT_TRACK proposal](https://donottrack.sh/) recommends honoring it **alongside your own controls**.

For your opt-in CLI, I’d support both: provide an explicit tool-specific opt-in and honor `DO_NOT_TRACK=1` as an overriding disable switch. For example:

```text
telemetry_enabled = explicit_opt_in && DO_NOT_TRACK != "1"
```

An unset `DO_NOT_TRACK`, or a value of `0`, should never count as consent. Document the precedence so users know the global opt-out wins.