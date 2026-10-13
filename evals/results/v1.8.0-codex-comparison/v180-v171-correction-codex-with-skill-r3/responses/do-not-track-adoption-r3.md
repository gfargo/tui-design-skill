**Define your own tool-specific control, and also honor `DO_NOT_TRACK=1`.** It’s a voluntary convention with limited adoption, not a universal standard those three tools follow.

Their documented opt-outs are:

| Tool | Environment variable |
|---|---|
| [Homebrew](https://docs.brew.sh/Analytics) | `HOMEBREW_NO_ANALYTICS=1` |
| [Gatsby](https://www.gatsbyjs.com/docs/telemetry/) | `GATSBY_TELEMETRY_DISABLED=1` |
| [.NET SDK](https://learn.microsoft.com/en-us/dotnet/core/tools/telemetry) | `DOTNET_CLI_TELEMETRY_OPTOUT=1` |

For your **opt-in** CLI, I recommend:

- Default telemetry to off; require explicit consent before collecting or sending anything.
- Provide `mycli telemetry enable`, `disable`, and `status`, plus `MYCLI_TELEMETRY_DISABLED=1`.
- Honor `DO_NOT_TRACK=1` as an absolute veto, even after prior consent.
- Skip telemetry in CI, and never send an event reporting that someone disabled telemetry.

Document these controls in `--help` and explain what you collect before asking for consent.