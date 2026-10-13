**Both use YAML.**

- **lazygit:** `config.yml` in its user configuration directory:
  - Linux: `~/.config/lazygit/config.yml` (or `$XDG_CONFIG_HOME/lazygit/config.yml`)
  - macOS: `~/Library/Application Support/lazygit/config.yml`
  - Windows: `%LOCALAPPDATA%\lazygit\config.yml`
  
  Run `lazygit --print-config-dir` to find the actual directory; `LG_CONFIG_FILE` can override the configuration file.

- **k9s plugins:** YAML too, conventionally `plugins.yaml` inside the k9s configuration directory—for example, `~/.config/k9s/plugins.yaml` on Linux. Run `k9s info` to see the resolved paths.

They share the file format, but their configuration schemas differ. See the [lazygit configuration docs](https://github.com/jesseduffield/lazygit/blob/master/docs/Config.md) and [k9s plugin docs](https://k9scli.io/topics/plugins/).