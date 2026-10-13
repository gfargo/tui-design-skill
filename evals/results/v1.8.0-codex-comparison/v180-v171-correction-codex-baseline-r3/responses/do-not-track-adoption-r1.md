`DO_NOT_TRACK=1` is a **community convention**, not a universal CLI standard—and those three tools document their own opt-outs:

| Tool | Documented opt-out |
|---|---|
| [Homebrew](https://docs.brew.sh/Analytics) | `HOMEBREW_NO_ANALYTICS=1` |
| [Gatsby](https://www.gatsbyjs.com/docs/telemetry/) | `GATSBY_TELEMETRY_DISABLED=1` |
| [.NET SDK](https://learn.microsoft.com/en-us/dotnet/core/tools/telemetry) | `DOTNET_CLI_TELEMETRY_OPTOUT=1` or `true` |

For your CLI, I’d **honor `DO_NOT_TRACK=1` and provide a tool-specific setting**. That supports both a global privacy preference and control over your CLI alone.

Since your telemetry is opt-in, keep it disabled until explicit consent, and let either opt-out override consent:

```text
enabled = explicitly_opted_in
          AND DO_NOT_TRACK != "1"
          AND tool_specific_opt_out_is_false
```

An unset `DO_NOT_TRACK`, or a value of `0`, should never count as consent.