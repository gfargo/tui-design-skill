Both use **YAML**, but their file names, locations and schemas differ. This is from memory rather than checked against current docs, so confirm against your installed versions with the commands below.

## lazygit

- **Format:** YAML, in a single file named `config.yml` (note the `.yml` extension).
- **Default location:**
  - Linux: `~/.config/lazygit/config.yml`
  - macOS: `~/Library/Application Support/lazygit/config.yml`. If `XDG_CONFIG_HOME` is set, it uses `$XDG_CONFIG_HOME/lazygit/config.yml` instead.
  - Windows: `%LOCALAPPDATA%\lazygit\config.yml`
- **Overrides:**
  - `CONFIG_DIR` changes the config directory.
  - `LG_CONFIG_FILE` takes a comma-separated list of config files, which are merged in order.
- **Per-repo config:** `<repo>/.git/lazygit.yml`, plus `.lazygit.yml` in parent directories. These are merged on top of the global config.
- **Extension point:** a `customCommands:` list inside the main config, with keys like `key`, `context`, `command`, `prompts`, `loadingText`.
- **Check it:** `lazygit --print-config-dir`

## k9s

- **Format:** also YAML, but with the `.yaml` extension. The main config is `config.yaml` (older versions used `config.yml`).
- **Plugins are a separate file**, not a section of the main config:
  - `$XDG_CONFIG_HOME/k9s/plugins.yaml`. On macOS without XDG set, this is `~/Library/Application Support/k9s/plugins.yaml`.
  - Newer versions also load individual plugin files from `$XDG_DATA_HOME/k9s/plugins/`.
  - `K9S_CONFIG_DIR` overrides the config directory.
- **Plugin schema example:**
  ```yaml
  plugins:
    my-plugin:
      shortCut: Shift-L
      description: Tail logs
      scopes: [pods]
      command: sh
      background: false
      confirm: false
      args: [-c, "kubectl logs -f $NAME -n $NAMESPACE"]
  ```
- **Check it:** `k9s info` prints the paths it actually resolves.

## Recommendations for your tool

1. **Use YAML and follow XDG.** Respect `XDG_CONFIG_HOME` on every platform, and offer an env var override like `YOURTOOL_CONFIG_DIR`. Both tools do this.
2. **Choose one extension and document it.** lazygit uses `.yml` and k9s uses `.yaml`. I'd use `.yaml` and also accept `.yml` as a fallback.
3. **Choose a plugin model:**
   - Inline like lazygit's `customCommands` is simpler.
   - A separate `plugins.yaml` or plugin directory like k9s is easier to share and drop in.
   - A good combination is inline config plus an optional plugin directory.
4. **Copy lazygit's layered merge** (global, then per-project, then env-specified files) if per-project settings matter to your users.
5. **Copy k9s's `scopes` field** for multi-pane tools. It limits a command to the panes or views where it makes sense.
