Both use **YAML**.

- **lazygit:** `config.yml` in its user configuration directory. Typically:
  - Linux: `~/.config/lazygit/config.yml` (or `$XDG_CONFIG_HOME/lazygit/config.yml`)
  - macOS: `~/Library/Application Support/lazygit/config.yml`
  - Windows: `%LOCALAPPDATA%\lazygit\config.yml`

  Run `lazygit --print-config-dir` to find the exact directory for your installation.

- **k9s plugins:** `plugins.yaml` in the k9s configuration directory—commonly `~/.config/k9s/plugins.yaml` on Linux. Run `k9s info` to see the actual paths.

For your tool, `config.yml` under a per-user, platform-appropriate config directory would mirror lazygit’s convention.