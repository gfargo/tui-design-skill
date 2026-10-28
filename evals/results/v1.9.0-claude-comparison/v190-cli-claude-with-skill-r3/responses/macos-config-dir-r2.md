Go's `os.UserConfigDir` doesn't look at `XDG_CONFIG_HOME` on macOS. That's how it's designed, not a bug in your code. It picks a path by OS:

| OS | What `os.UserConfigDir` returns |
|---|---|
| Linux / BSD | `$XDG_CONFIG_HOME` if set, otherwise `~/.config` |
| **macOS** | **`$HOME/Library/Application Support`** (never reads `XDG_CONFIG_HOME`) |
| Windows | `%AppData%` |

So on a Mac your tool reads `~/Library/Application Support/yourtool/`, whatever the user's environment says. Rust's `dirs`/`directories` crates work the same way.

## Fix: resolve the directory yourself

For a developer CLI on macOS, XDG (`~/.config/yourtool/`) is the better default. Users keep their dotfiles in sync across machines, and that's where they expect to find config. Use `~/Library/Application Support` for GUI-style apps.

```go
// configDir returns the directory holding yourtool's config.
// It honors XDG_CONFIG_HOME on every Unix, including macOS.
func configDir() (string, error) {
	if runtime.GOOS == "windows" {
		dir, err := os.UserConfigDir() // %AppData%
		if err != nil {
			return "", err
		}
		return filepath.Join(dir, "yourtool"), nil
	}
	// The XDG spec says to ignore relative paths.
	if x := os.Getenv("XDG_CONFIG_HOME"); x != "" && filepath.IsAbs(x) {
		return filepath.Join(x, "yourtool"), nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".config", "yourtool"), nil
}
```

Notes:

- **The absolute-path check matters.** Under the XDG spec, a relative `XDG_CONFIG_HOME` is invalid and must be ignored.
- **If you've already shipped the old behavior,** existing Mac users have config in `~/Library/Application Support/yourtool/`. Check that location as a legacy fallback, or migrate it once, and print a one-line notice so their settings don't silently disappear.
- **Library option:** `github.com/adrg/xdg` honors `XDG_*` on macOS when it's set. When it isn't set, though, its macOS defaults point to `~/Library/...` rather than `~/.config`. If you want `~/.config` everywhere, the hand-rolled version above is simpler.

## Make it easier to debug

Add a `--config PATH` flag and a `YOURTOOL_CONFIG` environment variable, with the flag taking priority. Also add a command that prints the resolved path and where each setting came from, for example `yourtool config list --show-origin`, in the style of `git config --show-origin`. With that, a user could see the problem right away instead of finding that their setting was ignored.
