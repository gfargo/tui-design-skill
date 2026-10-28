`os.UserConfigDir()` follows **OS-native conventions**, so it ignores `XDG_CONFIG_HOME` on macOS by design:

| OS | Config base |
|---|---|
| macOS | `$HOME/Library/Application Support` |
| Linux/other Unix | `$XDG_CONFIG_HOME`, otherwise `$HOME/.config` |
| Windows | `%AppData%` |

For a developer CLI that should use XDG paths on macOS, implement that policy explicitly:

```go
// Imports: "os", "path/filepath"
func configDir() (string, error) {
    if dir := os.Getenv("XDG_CONFIG_HOME"); filepath.IsAbs(dir) {
        return filepath.Join(dir, "mytool"), nil
    }

    home, err := os.UserHomeDir()
    if err != nil {
        return "", err
    }
    return filepath.Join(home, ".config", "mytool"), nil
}
```

This uses an absolute `XDG_CONFIG_HOME`, otherwise `~/.config/mytool`. Empty or relative values are ignored as required by XDG. Keep a separate Windows branch using `os.UserConfigDir()` if you support Windows.

For an existing CLI, document the path change and provide migration or fallback behavior so users’ current configs remain discoverable.