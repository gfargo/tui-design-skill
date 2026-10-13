No, those three don't follow it. `DO_NOT_TRACK=1` is a named convention, but few tools have adopted it. Homebrew, Gatsby and the .NET SDK each use their own variable instead:

| Tool | Opt-out variable |
|---|---|
| Homebrew | `HOMEBREW_NO_ANALYTICS` |
| Gatsby | `GATSBY_TELEMETRY_DISABLED` |
| .NET SDK | `DOTNET_CLI_TELEMETRY_OPTOUT` |

Netdata, Tilt and the GitHub CLI do honor `DO_NOT_TRACK`.

**Do both: define your own control and also respect `DO_NOT_TRACK`.**

- **Your own controls:** a tool-specific env var (e.g. `MYTOOL_TELEMETRY=0`) plus a subcommand like `mytool telemetry disable` that writes a config key. The GitHub CLI works this way with `GH_TELEMETRY` and a `telemetry` config key, and `GH_TELEMETRY` takes precedence over `DO_NOT_TRACK`.
- **Respect `DO_NOT_TRACK=1` too.** It's a single env lookup, and users who set it globally expect it to work.
- **Turn telemetry off in CI automatically.**
- **The opt-out always wins, and you check it before anything else.** Don't send anything once it's set, not even an event saying "user opted out." Netlify CLI was criticized for sending exactly that event.
- **Tell users before the first event.** Homebrew shows its analytics notice before sending anything, so people can opt out in advance.

Since your telemetry is opt-in, the main control is the opt-in itself: a `mytool telemetry enable` command or config key, off by default. The rules above still apply. `DO_NOT_TRACK=1` or your own opt-out variable should override an earlier opt-in, which covers shared machines and dotfiles where someone enabled it once. CI should stay off whatever the config says.

Source: the telemetry section of the skill's `references/cli-basics.md:472`.
