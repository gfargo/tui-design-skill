That’s expected: Go’s `os.UserConfigDir()` follows platform conventions, and **on macOS it doesn’t consult `XDG_CONFIG_HOME`**.

It returns:

| Platform | Config directory |
|---|---|
| macOS | `$HOME/Library/Application Support` |
| Linux/other Unix | `$XDG_CONFIG_HOME`, or `$HOME/.config` if unset |
| Windows | `%AppData%` |

If you want your CLI to honor `XDG_CONFIG_HOME` on macOS, implement that override explicitly:

```go
func configDir() (string, error) {
    if dir := os.Getenv("XDG_CONFIG_HOME"); dir != "" && filepath.IsAbs(dir) {
        return dir, nil
    }
    return os.UserConfigDir()
}
```

The absolute-path check follows the XDG specification, which says relative values should be ignored. Append your application’s directory name to the returned base directory.