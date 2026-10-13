Use the theme function adapter:

```go
form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

In v2, `ThemeCharm(true)` returns `*huh.Styles`, while `WithTheme` expects a `huh.Theme`. `ThemeFunc` wraps the function so Huh can supply the dark/light flag.

The form gets that flag from a **`tea.BackgroundColorMsg`**, using `msg.IsDark()`. There’s a caveat in **Huh v2.0.3**: it handles the reply but never requests it ([issue #834](https://github.com/charmbracelet/huh/issues/834)).

- **Embedded form:** return `tea.RequestBackgroundColor` from the parent’s `Init` and forward the reply to the form’s `Update`.
- **Standalone `form.Run()`:** detect the background before starting the form and pin the palette:

```go
isDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)

form.WithTheme(huh.ThemeFunc(func(bool) *huh.Styles {
    return huh.ThemeCharm(isDark)
}))
```

Use `charm.land/huh/v2` and `charm.land/lipgloss/v2`. Run that standalone detection before Bubble Tea starts; querying directly while it runs competes for terminal input.