That’s expected: Go’s `os.UserConfigDir()` follows platform conventions, and **on macOS it doesn’t consult `XDG_CONFIG_HOME`**.

It returns:

| Platform | Config directory |
|---|---|
| macOS | `$HOME/Library/Application Support` |
| Linux and other Unix systems | `$XDG_CONFIG_HOME`, falling back to `$HOME/.config` |
| Windows | `%AppData%` |

If you want your CLI to honor `XDG_CONFIG_HOME` on macOS, explicitly check it before calling `os.UserConfigDir()`:

```go
func configDir() (string, error) {
	if dir := os.Getenv("XDG_CONFIG_HOME"); dir != "" {
		if !filepath.IsAbs(dir) {
			return "", fmt.Errorf("XDG_CONFIG_HOME must be absolute")
		}
		return dir, nil
	}
	return os.UserConfigDir()
}
```

Then append your CLI’s directory name with `filepath.Join(dir, "mycli")`. This makes honoring XDG on macOS your CLI’s policy rather than Go’s default behavior.