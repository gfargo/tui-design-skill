Nothing is wrong with your code. That's how `os.UserConfigDir` is designed to work. It picks the directory by OS:

| OS | What `os.UserConfigDir()` returns |
|---|---|
| Linux / BSD | `$XDG_CONFIG_HOME`, or `~/.config` if it's unset |
| **macOS** | **`~/Library/Application Support`**. It never looks at `XDG_CONFIG_HOME` |
| Windows | `%AppData%` |

So on macOS your tool always goes to `~/Library/Application Support/yourtool`, even when the user has set `XDG_CONFIG_HOME`.

## Fix: check XDG yourself, then fall back

For a developer CLI on macOS, it's best to read `XDG_CONFIG_HOME` first and fall back to `~/.config`. Users expect this, and it lets them keep their dotfiles in sync across Mac and Linux. Leave `~/Library/Application Support` for GUI apps.

```go
func configDir(app string) (string, error) {
	// Honor XDG on every platform. The spec says relative paths are invalid and should be ignored.
	if x := os.Getenv("XDG_CONFIG_HOME"); x != "" && filepath.IsAbs(x) {
		return filepath.Join(x, app), nil
	}
	if runtime.GOOS == "windows" {
		d, err := os.UserConfigDir() // %AppData%
		if err != nil {
			return "", err
		}
		return filepath.Join(d, app), nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".config", app), nil
}
```

The macOS default changes with this fix: it becomes `~/.config/yourtool` instead of `~/Library/Application Support/yourtool`. If you've already shipped a release, existing users may have config in the old location. To avoid breaking them:

- **Read fallback:** if nothing exists at the new path, look at the old `os.UserConfigDir()` path too. You can also migrate the file over and print a one-time notice.
- **Make the location visible:** add a `yourtool config path` command, or a `--verbose` line that prints which file was loaded. That makes reports like this one quick to diagnose.

You'll run into the same issue with Rust's `dirs`/`directories` crates and with Python's `platformdirs` before version 4.6. Go also has other XDG-style helpers (`os.UserCacheDir` → `~/Library/Caches`), and they need the same handling. Check `XDG_CACHE_HOME`, `XDG_DATA_HOME` and `XDG_STATE_HOME` the same way, with fallbacks to `~/.cache`, `~/.local/share` and `~/.local/state`. If you'd rather not write this yourself, `github.com/adrg/xdg` handles it. On macOS it defaults to the Library paths too, but it does honor the environment variables when they're set.
