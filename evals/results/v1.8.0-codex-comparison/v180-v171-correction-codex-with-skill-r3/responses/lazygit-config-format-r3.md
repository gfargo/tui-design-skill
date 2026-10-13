**Lazygit uses YAML**, in a file named `config.yml`. Its default location depends on the OS:

| OS | Default path |
|---|---|
| Linux | `~/.config/lazygit/config.yml` (or `$XDG_CONFIG_HOME/lazygit/config.yml`) |
| macOS | `~/Library/Application Support/lazygit/config.yml` |
| Windows | `%LOCALAPPDATA%\lazygit\config.yml` |

Run `lazygit --print-config-dir` to find the actual directory; `LG_CONFIG_FILE` can override the configuration file.

**Yes, k9s plugins also use YAML**, in `plugins.yaml` within its configuration directory. Run `k9s info` to find that directory. The `.yml` and `.yaml` extensions indicate the same format, but the two apps have different configuration schemas.

For your tool, YAML in an app-specific configuration directory would mirror these conventions.