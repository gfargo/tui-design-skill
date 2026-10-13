Both tools use **YAML**, but they differ in file extension, location rules, and how they structure the config.

## lazygit

- **Format:** YAML, in one file called `config.yml` (note the `.yml` extension).
- **Default location:**
  - Linux: `~/.config/lazygit/config.yml` (follows `$XDG_CONFIG_HOME` if set)
  - macOS: `~/Library/Application Support/lazygit/config.yml`. If `XDG_CONFIG_HOME` is set, it uses `$XDG_CONFIG_HOME/lazygit/config.yml` instead.
  - Windows: `%APPDATA%\lazygit\config.yml`
- **Overrides:**
  - `CONFIG_DIR` changes the config directory.
  - `LG_CONFIG_FILE` points to specific file(s). It takes a comma-separated list, and later files are merged over earlier ones.
  - `lazygit --print-config-dir` shows the directory currently in use.
- **Per-repo config:** `<repo>/.git/lazygit.yml`, plus `.lazygit.yml` files in parent directories. These are layered on top of the global config.
- **Extensibility:** user commands go in a `customCommands:` **list** in the same file:
  ```yaml
  customCommands:
    - key: 'C'
      context: 'files'
      command: 'git commit -m "{{index .PromptResponses 0}}"'
      description: 'Quick commit'
      prompts:
        - type: 'input'
          title: 'Message'
  ```

## k9s

- **Format:** also YAML, but with the `.yaml` extension. Recent versions renamed `config.yml` to `config.yaml`.
- **Plugins live in their own file**, separate from the main config: `$XDG_CONFIG_HOME/k9s/plugins.yaml`.
  - Linux default: `~/.config/k9s/plugins.yaml`
  - macOS default: `~/Library/Application Support/k9s/plugins.yaml`, unless `XDG_CONFIG_HOME` is set
  - `K9S_CONFIG_DIR` overrides the directory. `k9s info` prints the paths in use.
  - Newer versions can also load one plugin per file from a `plugins/` directory under the k9s data dir.
- **Structure:** a **map keyed by plugin name** (lazygit uses a list):
  ```yaml
  plugins:
    stern-logs:
      shortCut: Ctrl-L
      description: Tail logs
      scopes: [pods]
      command: stern
      background: false
      confirm: false
      args: [--tail, "50", $NAME, -n, $NAMESPACE]
  ```
  Context comes from environment-style variables like `$NAME`, `$NAMESPACE` and `$CONTEXT`. lazygit uses Go templates like `{{.SelectedFile.Name}}` instead.

## Takeaways for your tool

- **YAML under an XDG-style directory** is the shared convention. Follow `$XDG_CONFIG_HOME` on all platforms, and provide an environment variable to override the directory.
- **Pick one extension and say so in the docs.** These two tools disagree (`.yml` vs `.yaml`), so it's worth accepting both.
- **Include a "print config path" command.** Both tools have one, and users depend on it.
- **Deciding where plugins go:** lazygit keeps them inline in the main config, while k9s puts them in a separate file. A separate file (or a directory of plugin files) makes plugins easier to share and version on their own.

All of this comes from memory, not from checking the current docs. Both projects have changed paths and filenames between versions (such as k9s's `.yml` → `.yaml` rename), so check the latest README or docs before you lock anything in.
