Both tools use **YAML**, but they lay out their files differently.

## lazygit

- **Format:** YAML, in a single file named `config.yml` (note the `.yml` extension).
- **Default location:**
  - **Linux:** `~/.config/lazygit/config.yml`, or `$XDG_CONFIG_HOME/lazygit/config.yml` if that variable is set.
  - **macOS:** `~/Library/Application Support/lazygit/config.yml`. If `XDG_CONFIG_HOME` is set, it uses `$XDG_CONFIG_HOME/lazygit/config.yml` instead.
  - **Windows:** `%LOCALAPPDATA%\lazygit\config.yml`. Older versions used `%APPDATA%`.
- **Overrides:**
  - `CONFIG_DIR` changes the config directory.
  - `LG_CONFIG_FILE` takes a comma-separated list of config files, which are merged in order.
  - `lazygit --print-config-dir` shows which directory is in use.
- **Per-repo config:** `.git/lazygit.yml` inside a repo, and `.lazygit.yml` in parent directories. These are merged on top of the global config.
- **Extensibility:** user commands live inside the main config under `customCommands:` (with `key`, `context`, `command`, `prompts`, etc.). There's no separate plugin file.

## k9s

- **Format:** also YAML, but with the **`.yaml`** extension. Since about v0.29 the main file is `config.yaml`; older versions used `config.yml`.
- **Location:** `$XDG_CONFIG_HOME/k9s/`. On macOS the default is `~/Library/Application Support/k9s/`. You can override it with `K9S_CONFIG_DIR`, and `k9s info` prints the paths in use.
- **Plugins:** kept separate from the main config:
  - `plugins.yaml` in the config dir, with a top-level `plugins:` map.
  - You can also put individual plugin files in `$XDG_DATA_HOME/k9s/plugins/`.
  - Each entry has `shortCut`, `description`, `scopes`, `command`, `args`, `background`, and `confirm`.
  - k9s also supports per-cluster/context config.

## Summary

| | lazygit | k9s |
|---|---|---|
| Format | YAML | YAML |
| Extension | `.yml` | `.yaml` |
| Base dir | XDG / OS app-support dir | XDG / OS app-support dir |
| Extensions/plugins | `customCommands:` inside `config.yml` | separate `plugins.yaml` (+ plugin dir) |
| Scoped overrides | per-repo files | per-cluster/context files |

**Recommendation:** to match lazygit, use YAML in `config.yml` under an XDG/OS-native config dir. Add an env var override and a `--print-config-dir` flag, and put custom commands inline in that file. If you expect lots of third-party extensions, k9s's separate plugins file and directory is worth borrowing, since it lets people drop in plugin files without editing the main config.

I wrote this from memory and didn't check it against current docs. Path details (especially the Windows paths and the k9s plugin directory) have changed between versions, so check them against the latest release before you finalize anything.
