Both use YAML, but they organize it differently.

**lazygit**
- **Format:** YAML, in a single file named `config.yml` (note the `.yml` extension).
- **Location** (from my own knowledge; the skill only names the file):
  - Linux: `~/.config/lazygit/config.yml`, or under `$XDG_CONFIG_HOME` if you've set it.
  - macOS: `~/Library/Application Support/lazygit/config.yml` by default. If `XDG_CONFIG_HOME` is set, it uses that instead.
  - Windows: `%LOCALAPPDATA%\lazygit\config.yml`.
  - Run `lazygit --print-config-dir` to see the path on your machine.
- **Overrides:** the `CONFIG_DIR` environment variable changes the directory. `LG_CONFIG_FILE` takes a comma-separated list of files that are merged in order. Per-repo overrides go in `<repo>/.git/lazygit.yml`, or in `.lazygit.yml` in a parent directory.
- **Extensions:** lazygit has no separate plugin file. User actions go in a `customCommands:` list inside `config.yml`. Each entry has a key, a context (the pane it applies to), a command template, and optional prompts.

**k9s**
- **Format:** also YAML, but plugins live in their own file, `plugins.yaml` (note the `.yaml` extension). The main config is `config.yaml`, also separate.
- **Location:** `$XDG_CONFIG_HOME/k9s/`, overridable with `K9S_CONFIG_DIR`. Like lazygit, the macOS default falls back to `~/Library/Application Support/k9s/`. Run `k9s info` to print the paths it uses. Recent versions can also load individual plugin files from a plugins directory, and plugins can be set per cluster or context. Check the k9s docs for your version, because these paths changed around v0.29.
- **Plugin shape:** each plugin has a `shortCut`, a list of `scopes` (the resource types it applies to), and a `command` plus `args`, which can use variables such as `$NAME` and `$NAMESPACE`.

**What I'd do for your tool**
- **Format:** use YAML so it feels familiar to users of the lazy* tools (lazygit, lazydocker) and k9s. Pick one extension, `.yml` or `.yaml`, and stick to it. Ideally accept both when reading.
- **Location:** use `~/.config/<tool>/` on every OS, macOS included. The skill recommends XDG paths for developer tools so people's dotfiles stay portable. lazygit's macOS default of `~/Library/Application Support` is the part of its approach I wouldn't copy.
- **Custom actions:** if they're small, follow lazygit and put them inside the main config. If you expect people to share or drop in action packs, give them a separate file like k9s's `plugins.yaml`.
- **Overrides:** support an environment variable that changes the config directory, and a per-project override file. Order of precedence should be flag, then environment, then project config, then user config, then built-in defaults.
- **Discovery:** add a `--print-config-dir` flag (or similar) so users can find the file.

Sources: the skill confirms both tools use YAML, plus lazygit's `config.yml` and k9s's `plugins.yaml`. It doesn't give exact file paths or override variables, so those come from my own knowledge. Check them against each project's docs before you copy them.
