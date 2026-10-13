**Define your own opt-out, and also honor `DO_NOT_TRACK=1`.** It’s a voluntary convention with limited adoption, not a universal CLI standard those three tools follow.

Their documented controls are:

| Tool | Telemetry opt-out |
|---|---|
| [Homebrew](https://docs.brew.sh/Analytics) | `HOMEBREW_NO_ANALYTICS=1` or `brew analytics off` |
| [Gatsby](https://www.gatsbyjs.com/docs/telemetry/) | `GATSBY_TELEMETRY_DISABLED=1` or `gatsby telemetry --disable` |
| [.NET SDK](https://learn.microsoft.com/en-us/dotnet/core/tools/telemetry) | `DOTNET_CLI_TELEMETRY_OPTOUT=1` or `true` |

For your **opt-in** design:

- Keep telemetry off until the user explicitly enables it; disclose what you collect first.
- Provide `MYCLI_TELEMETRY_DISABLED=1` and `mycli telemetry disable`.
- Make either that variable or `DO_NOT_TRACK=1` veto collection, even after prior consent.
- Skip telemetry in CI, and never send an event reporting that someone opted out.

The absence of an opt-out variable must never count as consent.