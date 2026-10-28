That's how `os.UserConfigDir` is designed: it only checks `XDG_CONFIG_HOME` on Linux and other non-Darwin Unix systems. Per OS it does this:

| OS | Returns |
|---|---|
| Linux / BSD (Unix) | `$XDG_CONFIG_HOME` if set, else `$HOME/.config` |
| **macOS (darwin)** | **`$HOME/Library/Application Support`**, always |
| Windows | `%AppData%` |
| Plan 9 | `$home/lib` |

On darwin the standard library ignores `XDG_CONFIG_HOME` completely. That's because the platform convention is `~/Library/Application Support`, not XDG.

## Fix: check XDG yourself first

Many CLI tools (gh, git, helix, etc.) honour XDG on macOS because CLI users expect it. You can do the same:

```go
func configDir() (string, error) {
	// Honour XDG on every platform, including macOS.
	if dir := os.Getenv("XDG_CONFIG_HOME"); dir != "" && filepath.IsAbs(dir) {
		return filepath.Join(dir, "mytool"), nil
	}
	base, err := os.UserConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(base, "mytool"), nil
}
```

The `filepath.IsAbs` check matches the XDG spec, which says to ignore relative paths. The stdlib does the same check on Linux.

## Optional: use `~/.config` on macOS too

Many macOS CLI users prefer `~/.config/mytool` even when `XDG_CONFIG_HOME` isn't set. If you want that:

```go
if runtime.GOOS == "darwin" {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".config", "mytool"), nil
}
```

If you already have users with config in `~/Library/Application Support/mytool`, keep reading from there as a fallback when the new path doesn't exist, so their settings aren't lost.

**Libraries:** `github.com/adrg/xdg` follows XDG on macOS, but its default config location there is `~/Library/Application Support`. If you only need this one path, the snippet above is simpler than adding a dependency.
