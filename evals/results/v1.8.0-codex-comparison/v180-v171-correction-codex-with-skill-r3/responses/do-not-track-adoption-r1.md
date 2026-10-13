**Define your own tool-specific control, and also honor `DO_NOT_TRACK=1`.** It’s a convention with limited adoption, not a universal standard followed by those three tools.

| Tool | Documented telemetry opt-out |
|---|---|
| [Homebrew](https://docs.brew.sh/Analytics) | `HOMEBREW_NO_ANALYTICS=1` or `brew analytics off` |
| [Gatsby](https://www.gatsbyjs.com/docs/telemetry/) | `GATSBY_TELEMETRY_DISABLED=1` or `gatsby telemetry --disable` |
| [.NET SDK](https://learn.microsoft.com/en-us/dotnet/core/tools/telemetry) | `DOTNET_CLI_TELEMETRY_OPTOUT=1` or `true` |

Following the tui-design skill’s CLI guidance, I’d provide `MYCLI_TELEMETRY_DISABLED=1` plus `mycli telemetry enable|disable|status`, and honor `DO_NOT_TRACK=1` as an additional veto.

Since yours is **opt-in**, keep telemetry off until explicit consent. Check disable signals before collecting or sending anything, let them override saved consent, and never send an event reporting that telemetry was disabled.