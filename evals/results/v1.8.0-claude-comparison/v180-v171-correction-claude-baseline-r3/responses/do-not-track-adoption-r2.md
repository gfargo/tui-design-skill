Not quite. `DO_NOT_TRACK=1` is a real convention, but it's a grassroots proposal (from consoledonottrack.com), not a formal standard. The three tools you named are known mainly for their **own** opt-out variables:

| Tool | Its own opt-out |
|---|---|
| Homebrew | `HOMEBREW_NO_ANALYTICS=1` |
| Gatsby | `GATSBY_TELEMETRY_DISABLED=1` |
| .NET SDK | `DOTNET_CLI_TELEMETRY_OPTOUT=1` |

I'm not sure whether each one also honors `DO_NOT_TRACK`, and support has changed over time. If you plan to cite them as precedent, check their current docs. Either way, you can't count on `DO_NOT_TRACK` being universal.

**My recommendation is to support both:**

1. **Honor `DO_NOT_TRACK`.** It's free to add, some users set it globally in their shell, and respecting it builds trust.
2. **Define your own variable**, like `MYCLI_TELEMETRY_DISABLED=1`. It's easy to find in your docs, it's specific to your tool, and it's what most established CLIs do.
3. **Make the opt-out always win.** If either variable is set to a truthy value, telemetry stays off, even if the user opted in through your config or a prompt.

Since your telemetry is opt-in, these variables aren't the main control, because the default is already off. They're a hard override, which matters most in CI and shared environments. A few other things worth doing:

- Treat `1` and `true` as truthy, and consider any non-empty value except `0` or `false` as truthy too.
- Never send anything before the user has explicitly consented. That includes a "user opted out" ping.
- Consider leaving telemetry off when `CI` is set, unless the user explicitly opted in.
- Add a command like `mycli telemetry status` that shows which setting is in effect and why.
