In Huh v2, `WithTheme` takes a `huh.Theme` interface instead of a `*huh.Theme` struct. The built-in themes are now plain functions with the signature `func(isDark bool) *huh.Styles`, so you wrap them in the `huh.ThemeFunc` adapter and pass the function itself without calling it:

```go
form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

Here's the interface, from `charm.land/huh/v2@v2.0.3/theme.go:10`:

```go
type Theme interface {
	Theme(isDark bool) *Styles
}

type ThemeFunc func(isDark bool) *Styles
```

## How the form learns whether the background is dark

The form doesn't decide at construction time anymore. The form, each group and each field keep a `hasDarkBg` flag. Each one sets it when a `tea.BackgroundColorMsg` arrives (`form.go:537`: `f.hasDarkBg = msg.IsDark()`). On every render it calls `theme.Theme(hasDarkBg)` to get the styles (`form.go:642`).

The catch is that something has to request that message, and in v2.0.3 the form never does. `Form.Init` only sends `tea.RequestWindowSize` (`form.go:523`). In the whole module, only the `spinner` package calls `tea.RequestBackgroundColor`. Bubble Tea v2.1.0 also doesn't query the terminal on its own; it only does so when it gets that command (`bubbletea tea.go:846`). So `hasDarkBg` stays `false` until a message arrives, and the light palette is used.

How to handle that depends on how you run the form.

**Form embedded in your own Bubble Tea model:** request the color yourself and pass messages through to the form, which forwards them to the active group:

```go
func (m model) Init() tea.Cmd {
	return tea.Batch(m.form.Init(), tea.RequestBackgroundColor)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	f, cmd := m.form.Update(msg) // passes BackgroundColorMsg through
	// ...
}
```

**Standalone `form.Run()`:** there's no way to add an init command, so detect the background before starting and ignore the flag the form passes in:

```go
isDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)

form.WithTheme(huh.ThemeFunc(func(bool) *huh.Styles {
	return huh.ThemeCharm(isDark)
}))
```

The huh spinner uses the same `lipgloss.HasDarkBackground(tin, tout)` call for its non-TUI path (`spinner/spinner.go:268`).

I worked this out from the v2.0.3 source in your module cache and didn't run a test program. If you're on a different version, check whether `Form.Init` now requests the background color before using the workaround.
