Not quite. **`DO_NOT_TRACK` isn't a formal standard, and those three tools are mainly known for their own variables:**

| Tool | Documented opt-out |
|---|---|
| Homebrew | `HOMEBREW_NO_ANALYTICS=1` (or `brew analytics off`) |
| Gatsby | `GATSBY_TELEMETRY_DISABLED=1` (or `gatsby telemetry --disable`) |
| .NET SDK | `DOTNET_CLI_TELEMETRY_OPTOUT=1` |

`DO_NOT_TRACK=1` comes from a community proposal (consoledonottrack.com). Some CLIs honor it, but adoption is patchy. I'm not sure whether any of these three check it today. That may have changed, so look at their current docs before saying they do.

**What I'd do: support both.**

1. **Define your own variable**, e.g. `MYCLI_TELEMETRY_DISABLED=1`. Users expect a tool-specific switch, and it's the clearest thing to document.
2. **Also honor `DO_NOT_TRACK`** as a global kill switch. It costs one line and respects users who set it once for all their tools.
3. Treat either one as a hard override that beats any stored consent. Accept `1`/`true` and ignore case.

```js
const truthy = v => v && !['0', 'false', ''].includes(v.toLowerCase());
const telemetryDisabled =
  truthy(process.env.DO_NOT_TRACK) || truthy(process.env.MYCLI_TELEMETRY_DISABLED);
```

Since your telemetry is opt-in, nothing should be sent until the user explicitly agrees. The env vars still help, though:
- They suppress the consent prompt in scripts and CI. You might also skip the prompt when `CI` is set or stdin isn't a TTY.
- They let admins block telemetry across a machine or fleet, whatever individual users choose.
