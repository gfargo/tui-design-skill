**Short answer:** both use YAML. lazygit keeps its settings in `config.yml`, and k9s puts plugins in a separate `plugins.yaml`. Note the different extensions, `.yml` and `.yaml`.

**What the skill's reference notes say** (`references/exemplar-apps.md:49`, `:70`, and `references/visual-patterns.md:629`):
- **lazygit:** YAML config in `config.yml`. Custom commands and aliases are defined there too, not in a separate file.
- **k9s:** YAML for its main config. The plugin system for custom actions lives in its own `plugins.yaml`.

**File locations.** The skill doesn't cover these, so this comes from my own knowledge. Run each tool's command below to confirm on your machine:

| | lazygit | k9s |
|---|---|---|
| Linux | `~/.config/lazygit/config.yml` | `~/.config/k9s/` (`config.yaml`, `plugins.yaml`, `skins/`) |
| macOS default | `~/Library/Application Support/lazygit/config.yml` (uses `$XDG_CONFIG_HOME` if set) | `~/Library/Application Support/k9s/` (uses `$XDG_CONFIG_HOME` if set) |
| Override | `CONFIG_DIR`; `LG_CONFIG_FILE` (accepts a comma-separated list of files) | `K9S_CONFIG_DIR` |
| Print the path | `lazygit --print-config-dir` | `k9s info` |

**Recommendations for your tool:**
1. **Use YAML** so lazygit and k9s users find it familiar. Pick one extension and stick to it. Ideally accept both `.yml` and `.yaml` so people who mix them up aren't caught out.
2. **Keep custom commands in the main config**, the way lazygit does. Only split them into a separate `plugins.yaml` (the k9s approach) if plugins get large or users will share them independently.
3. **Default to `$XDG_CONFIG_HOME/yourtool/`**, falling back to `~/.config/yourtool/`, on macOS as well as Linux. The skill's `references/cli-basics.md:348-350` recommends XDG over `~/Library/Application Support/` for developer CLIs because it keeps dotfiles portable. Both lazygit and k9s default to `~/Library` on macOS, and that annoys people who sync their dotfiles.
4. **Add an env-var override** (`YOURTOOL_CONFIG_DIR`) and a command that prints the config path. Both apps have one, and it saves a lot of support questions.
5. **Define the schema early** (`visual-patterns.md:100`). Users of multi-pane tools will want to change keybindings, themes and layout. A published JSON Schema also gives them editor autocomplete for YAML, which lazygit offers too.
