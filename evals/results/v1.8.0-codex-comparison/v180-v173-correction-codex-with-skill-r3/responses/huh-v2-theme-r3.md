Use the function adapter, without calling `ThemeCharm` yourself:

```go
form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

In v2, `ThemeCharm(isDark bool)` returns `*huh.Styles`, while `WithTheme` expects a `huh.Theme`. `ThemeFunc` bridges those types.

The form gets `isDark` from a Bubble Tea `tea.BackgroundColorMsg`. **Huh v2.0.3 handles that reply but doesn’t request it** ([issue #834](https://github.com/charmbracelet/huh/issues/834)):

- **Embedded form:** return `tea.RequestBackgroundColor` from the parent’s `Init`—alongside the form’s initialization command—and forward the resulting messages to the form.
- **Standalone `form.Run()`:** it defaults to the light variant. Detect the background before starting the form and pin the result:

```go
isDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)

form.WithTheme(huh.ThemeFunc(func(bool) *huh.Styles {
    return huh.ThemeCharm(isDark)
}))

err := form.Run()
```

Use `charm.land/huh/v2` and `charm.land/lipgloss/v2`. Call `HasDarkBackground` before Bubble Tea runs; querying it during a running program competes for terminal input.