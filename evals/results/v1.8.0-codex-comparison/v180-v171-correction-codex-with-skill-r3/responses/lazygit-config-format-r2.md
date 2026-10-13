Lazygit uses **YAML**, in a file named `config.yml`. Its default location depends on the OS:

| OS | Default path |
|---|---|
| Linux | `~/.config/lazygit/config.yml` (or `$XDG_CONFIG_HOME/lazygit/config.yml`) |
| macOS | `~/Library/Application Support/lazygit/config.yml` |
| Windows | `%LOCALAPPDATA%\lazygit\config.yml` |

Run `lazygit --print-config-dir` to find the actual directory. Lazygit also supports a `--use-config-file` override.

**Yes, k9s plugins also use YAML**, conventionally named `plugins.yaml` in the k9s configuration directory. The `.yml` and `.yaml` extensions represent the same format, but the two apps use different schemas.