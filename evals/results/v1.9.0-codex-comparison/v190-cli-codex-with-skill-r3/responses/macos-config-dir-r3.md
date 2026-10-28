`os.UserConfigDir()` follows **platform conventions**, so on macOS it ignores `XDG_CONFIG_HOME` and returns `$HOME/Library/Application Support`. On Linux, it honors `XDG_CONFIG_HOME`, falling back to `$HOME/.config`. This is expected behavior ([Go docs](https://pkg.go.dev/os#UserConfigDir)).

For a developer CLI that follows XDG on macOS too, resolve the directory explicitly:

```go
// Imports: os, path/filepath
func configDir() (string, error) {
    base := os.Getenv("XDG_CONFIG_HOME")
    if base == "" || !filepath.IsAbs(base) {
        home, err := os.UserHomeDir()
        if err != nil {
            return "", err
        }
        base = filepath.Join(home, ".config")
    }
    return filepath.Join(base, "mytool"), nil
}
```

XDG requires absolute paths; empty or relative values fall back to `~/.config`. Keep `os.UserConfigDir()` for Windows if you want its native `%AppData%` convention.

If users already have configs under `~/Library/Application Support/mytool`, provide a documented migration or legacy lookup when changing this behavior.