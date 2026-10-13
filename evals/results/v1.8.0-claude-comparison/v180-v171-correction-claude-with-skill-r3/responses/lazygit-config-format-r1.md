**Short answer:** Both use YAML, but they organize it differently. lazygit keeps everything, including custom commands, in one `config.yml`. k9s puts plugins in their own `plugins.yaml`, separate from its main `config.yaml`.

## lazygit

- **Format:** YAML, in a single file named `config.yml` (note the `.yml` extension).
- **Default location:**
  - Linux: `~/.config/lazygit/config.yml`, or under `$XDG_CONFIG_HOME` if set
  - macOS: `~/Library/Application Support/lazygit/config.yml`, unless `XDG_CONFIG_HOME` is set, in which case it uses that
  - Windows: `%LOCALAPPDATA%\lazygit\config.yml`
- **Overrides:**
  - `CONFIG_DIR` changes the config directory.
  - `LG_CONFIG_FILE` takes a comma-separated list of files that are merged in order.
  - Repo-local overrides go in `.git/lazygit.yml`, or in `.lazygit.yml` in a parent directory.
- **Finding the path:** `lazygit --print-config-dir`
- **Custom commands** are not a separate file. They go under a `customCommands:` list inside `config.yml`, with each entry setting `key`, `context`, `command`, and optional `prompts`.

## k9s

- **Format:** YAML as well (`.yaml` extension), but split across several files:
  - `config.yaml` for main settings
  - `plugins.yaml` for plugins
  - `aliases.yaml`, `hotkeys.yaml`, and `views.yaml` for other features
- **Location:** `$XDG_CONFIG_HOME/k9s/`, which defaults to `~/.config/k9s/` on Linux. macOS has the same Application Support behavior as lazygit. Override it with `K9S_CONFIG_DIR`.
- **Finding the paths:** `k9s info`
- **Plugin shape:** a top-level `plugins:` map keyed by name. Each entry has `shortCut`, `scopes` (which resource views it applies to), `command`, `args`, `background`, and `confirm`. Newer versions also load plugin files from a plugins directory under the data dir and from per-context config.

## What to copy for your tool

- **Use YAML.** It's what lazygit, lazydocker, and k9s use, so their users will expect it.
- **Store config under `~/.config/<tool>/`, even on macOS.** Both apps default to `~/Library/Application Support` on macOS, which users often find annoying. For a developer CLI, `~/.config` keeps dotfiles portable between machines.
- **Pick one layout for user commands:**
  - lazygit style: commands live inside `config.yml`. One file is easier to discover.
  - k9s style: commands get their own `plugins.yaml`. This is easier to share and drop in.

  For a lazygit-style tool, I'd keep commands inline under a `customCommands:` key, scoped by pane or context the way lazygit's `context:` field works.
- **Precedence:** flags, then env vars (`<TOOL>_CONFIG_DIR`), then repo-local file, then user config, then defaults.
- **Add a flag that prints the resolved config path,** like `--print-config-dir` or `info`. Both tools have one, and it saves users a lot of guessing.

The YAML format for both comes from the skill's references. The exact paths, env var names, and field names are from my own knowledge of these tools, not the skill. Check them against the current lazygit `docs/Config.md` and the k9s plugin docs before you rely on them.
