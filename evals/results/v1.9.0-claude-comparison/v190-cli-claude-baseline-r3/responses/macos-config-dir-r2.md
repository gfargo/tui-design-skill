This is how `os.UserConfigDir` is designed to work. It only reads `XDG_CONFIG_HOME` on Unix-like systems other than macOS.

From the Go source (`os/file.go`):

| OS | What it returns |
|---|---|
| Linux/BSD (Unix) | `$XDG_CONFIG_HOME` if set, else `$HOME/.config` |
| **darwin (macOS)** | **`$HOME/Library/Application Support`** (never checks `XDG_CONFIG_HOME`) |
| Windows | `%AppData%` |
| Plan 9 | `$home/lib` |

Go follows each platform's native convention. On macOS, the native place for config is `~/Library/Application Support`, and XDG is treated as a Linux/freedesktop thing. That's why your macOS user's setting has no effect.

## Fix: check XDG first, then fall back

Many CLI tools on macOS (git, gh, nvim, etc.) honor `XDG_CONFIG_HOME` when it's set, and macOS CLI users often expect that. Wrap the call:

```go
func configDir() (string, error) {
	if dir := os.Getenv("XDG_CONFIG_HOME"); dir != "" {
		if !filepath.IsAbs(dir) {
			return "", errors.New("XDG_CONFIG_HOME must be an absolute path")
		}
		return dir, nil
	}
	return os.UserConfigDir()
}
```

The absolute-path check matches the XDG spec and what Go does on Linux.

## Things to decide

- **Fallback on macOS:** with the code above, users who don't set XDG still get `~/Library/Application Support/yourtool`. Many CLI tools fall back to `~/.config/yourtool` on macOS instead, because users find it easier to locate and put in their dotfiles. If you want that:
  ```go
  if runtime.GOOS == "darwin" {
      home, err := os.UserHomeDir()
      if err != nil { return "", err }
      return filepath.Join(home, ".config"), nil
  }
  ```
- **Existing users:** if you change the path, check the old `Library/Application Support` location too and either read from it or migrate it, so current configs don't silently disappear.
- **Library option:** [`github.com/adrg/xdg`](https://github.com/adrg/xdg) handles this for every platform if you'd rather not write it yourself. On macOS it also honors `XDG_CONFIG_HOME`.
