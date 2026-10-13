**`DO_NOT_TRACK=1` is a voluntary cross-tool convention, not a universal CLI standard.** Those three tools document their own opt-outs:

| Tool | Documented opt-out |
|---|---|
| [Homebrew](https://docs.brew.sh/Analytics) | `HOMEBREW_NO_ANALYTICS=1` or `brew analytics off` |
| [Gatsby](https://www.gatsbyjs.com/docs/telemetry/) | `GATSBY_TELEMETRY_DISABLED=1` or `gatsby telemetry --disable` |
| [.NET SDK](https://learn.microsoft.com/en-us/dotnet/core/tools/telemetry) | `DOTNET_CLI_TELEMETRY_OPTOUT=1` or `true` |

For your CLI, I’d **support both `DO_NOT_TRACK=1` and a tool-specific opt-out**, such as `MYCLI_TELEMETRY_DISABLED=1`. That gives users a global preference and a targeted control.

Since your telemetry is **opt-in**, keep it disabled until users explicitly consent. Either opt-out should override that consent; absence of `DO_NOT_TRACK` is never consent.

I couldn’t verify the live documentation in this session, so the table reflects the documented conventions I know.