`os.UserConfigDir()` follows **OS-specific conventions**. On macOS it returns `$HOME/Library/Application Support` and ignores `XDG_CONFIG_HOME`. On Linux/other Unix systems, it honors that variable.

For a developer CLI that uses XDG paths on macOS, resolve them explicitly:

```go
func configDir() (string, error) {
    if runtime.GOOS == "windows" {
        return os.UserConfigDir()
    }
    if dir := os.Getenv("XDG_CONFIG_HOME"); dir != "" && filepath.IsAbs(dir) {
        return dir, nil
    }
    home, err := os.UserHomeDir()
    if err != nil {
        return "", err
    }
    return filepath.Join(home, ".config"), nil
}
```

Imports: `os`, `path/filepath`, `runtime`. Append your app’s directory with `filepath.Join(base, "mytool")`.

XDG requires an **absolute path**; ignore relative values. This policy also makes the macOS fallback `~/.config/mytool`. If existing users have config under `Library/Application Support`, provide a documented fallback or migration.