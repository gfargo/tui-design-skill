`os.UserConfigDir()` follows **platform-specific conventions**, so it doesn’t honor `XDG_CONFIG_HOME` on macOS.

Its behavior is:

| Platform | Config directory |
|---|---|
| macOS | `$HOME/Library/Application Support` |
| Linux and most other Unix systems | `$XDG_CONFIG_HOME`, falling back to `$HOME/.config` |
| Windows | `%AppData%` |

If you want your CLI to honor `XDG_CONFIG_HOME` on macOS, implement that precedence yourself:

```go
func configDir() (string, error) {
    if dir := os.Getenv("XDG_CONFIG_HOME"); dir != "" && filepath.IsAbs(dir) {
        return dir, nil
    }
    return os.UserConfigDir()
}
```

The absolute-path check follows the XDG specification, which says relative values should be ignored. Then append your app’s directory with `filepath.Join(dir, "your-cli")`.