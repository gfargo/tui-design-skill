Lazygit uses **YAML**, in a file named `config.yml`. Its default location depends on the OS:

| OS | Default location |
|---|---|
| Linux | `~/.config/lazygit/config.yml` |
| macOS | `~/Library/Application Support/lazygit/config.yml` |
| Windows | `%LOCALAPPDATA%\lazygit\config.yml` |

On Linux, `$XDG_CONFIG_HOME` replaces `~/.config` when set. Run `lazygit --print-config-dir` to find the actual directory; `LG_CONFIG_DIR` can override it.

**Yes, k9s plugins also use YAML**, typically in `plugins.yaml` inside the k9s configuration directory. Run `k9s info` to locate that directory.

The formats match, but the schemas differ: lazygit defines custom actions under `customCommands`, while k9s defines them under `plugins`.