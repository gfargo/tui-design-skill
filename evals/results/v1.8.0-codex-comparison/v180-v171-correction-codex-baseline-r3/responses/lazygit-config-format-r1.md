Both use **YAML**, though their configuration schemas differ.

**Lazygit** uses `config.yml`, normally located at:

| Platform | Default path |
|---|---|
| Linux | `~/.config/lazygit/config.yml` |
| macOS | `~/Library/Application Support/lazygit/config.yml` |
| Windows | `%LOCALAPPDATA%\lazygit\config.yml` |

Paths can vary with environment settings or older installations. Run `lazygit --print-config-dir` to get the actual directory; `LG_CONFIG_FILE` can override the configuration file.

**k9s plugins** also use YAML, in `plugins.yaml` inside the k9s configuration directory—typically `~/.config/k9s/plugins.yaml` on Linux. Run `k9s info` to find its directories.

For your tool, `config.yml` under an application-specific configuration directory would mirror lazygit’s convention.

References: [lazygit configuration](https://github.com/jesseduffield/lazygit/blob/master/docs/Config.md), [k9s plugins](https://k9scli.io/topics/plugins/).