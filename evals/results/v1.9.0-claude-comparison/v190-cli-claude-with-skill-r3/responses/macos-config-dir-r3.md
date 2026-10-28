The problem isn't in your code. That's how `os.UserConfigDir` works on macOS.

**Why:** `os.UserConfigDir` follows each operating system's own conventions:

| OS | Returns | Checks `XDG_CONFIG_HOME`? |
|---|---|---|
| Linux / BSD | `$XDG_CONFIG_HOME`, else `~/.config` | Yes |
| macOS | `~/Library/Application Support` | **No** |
| Windows | `%AppData%` | No |

On macOS the function never reads `XDG_CONFIG_HOME`, so your user's setting has no effect. Your config is being read from `~/Library/Application Support/<tool>/` instead.

**What to do:** For a developer CLI, use XDG on macOS too. Many users keep `~/.config` in a dotfiles repo they share across machines, and `~/Library/Application Support` is really meant for GUI apps. You'll need to look up the path yourself:

```go
func configDir(app string) (string, error) {
	// Honor XDG_CONFIG_HOME on every platform; the spec says relative paths are invalid.
	if dir := os.Getenv("XDG_CONFIG_HOME"); dir != "" && filepath.IsAbs(dir) {
		return filepath.Join(dir, app), nil
	}
	if runtime.GOOS == "windows" {
		dir, err := os.UserConfigDir() // %AppData%
		if err != nil {
			return "", err
		}
		return filepath.Join(dir, app), nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".config", app), nil
}
```

Things to watch out for:

- **Migration:** If you've already shipped a release, some macOS users have config files in `~/Library/Application Support/<tool>/`. For a release or two, check that path as a fallback, and print a one-line notice on stderr pointing to the new location. Without that, their settings will seem to disappear.
- **Libraries:** `github.com/adrg/xdg` reads `XDG_CONFIG_HOME` when it's set. When it isn't, it still defaults to `~/Library/Application Support` on macOS, so if you want `~/.config` there you'd still need the fallback logic above.
- **Make it visible:** Show the resolved path in something like `mytool config path` or `--version --verbose`. Then the next "my setting is ignored" report takes one command to diagnose.

The same thing happens with Rust's `dirs`/`directories` crates and with Python's `platformdirs` before version 4.6.
