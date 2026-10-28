Because that's how `os.UserConfigDir` is built. On macOS it never looks at `XDG_CONFIG_HOME`. The standard library picks the directory based on the OS:

| OS | What `os.UserConfigDir` returns |
|---|---|
| Linux / BSD (other Unix) | `$XDG_CONFIG_HOME` if set, otherwise `$HOME/.config` |
| **macOS (darwin)** | **`$HOME/Library/Application Support`** (always) |
| Windows | `%AppData%` |
| Plan 9 | `$home/lib` |

The darwin branch only reads `$HOME`. XDG is a freedesktop.org convention, not a macOS one, so Go follows Apple's guidelines there. This is intended behavior, not a bug.

### Fixes

**Option 1: Check XDG first, then fall back to the OS default.** This is what most CLIs do, and it's what users who set `XDG_CONFIG_HOME` expect:

```go
func configDir() (string, error) {
	if dir := os.Getenv("XDG_CONFIG_HOME"); dir != "" {
		if !filepath.IsAbs(dir) {
			return "", errors.New("XDG_CONFIG_HOME must be an absolute path")
		}
		return filepath.Join(dir, "mytool"), nil
	}
	base, err := os.UserConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(base, "mytool"), nil
}
```

(The absolute-path check matches the XDG spec and how Go treats the variable on Linux.)

**Option 2: Use `~/.config` on macOS too.** Many developer CLIs (gh, git, and others) do this, because people expect dotfiles in `~/.config` even on a Mac. Check `XDG_CONFIG_HOME`, then fall back to `$HOME/.config` instead of `Library/Application Support`.

**Option 3: Use a library.** [`github.com/adrg/xdg`](https://github.com/adrg/xdg) handles XDG variables on every platform. Note that its macOS defaults still point at `~/Library/...` unless the env vars are set.

### Migration note
If you already ship a version that wrote to `~/Library/Application Support/mytool`, keep reading from that path as a fallback, or migrate it. Otherwise existing macOS users will lose their config when you switch.

I'd go with Option 1, and pick Option 2 instead if your users are mostly developers who manage dotfiles.
