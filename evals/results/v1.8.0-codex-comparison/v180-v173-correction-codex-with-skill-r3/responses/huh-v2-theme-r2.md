Use the theme function adapter:

```go
form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

In v2, `ThemeCharm(bool)` returns `*huh.Styles`, while `WithTheme` expects a `huh.Theme`. `ThemeFunc` bridges those types.

Huh supplies the boolean from `tea.BackgroundColorMsg`, using `msg.IsDark()`. **In Huh v2.0.3, the form handles that message but never requests it** ([issue #834](https://github.com/charmbracelet/huh/issues/834)):

- **Embedded form:** return `tea.RequestBackgroundColor` from the parent’s `Init`—batch it with other initialization commands—and forward the resulting message to `form.Update`.
- **Standalone `form.Run()`:** it otherwise uses the light variant. Detect the background before starting the form and pin the palette:

```go
// Imports: "os", "charm.land/huh/v2", "charm.land/lipgloss/v2"
isDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)

form.WithTheme(huh.ThemeFunc(func(bool) *huh.Styles {
    return huh.ThemeCharm(isDark)
}))
err := form.Run()
```

Call `HasDarkBackground` before Bubble Tea runs; during a running program, use its background-color message so the two don’t compete for terminal input.