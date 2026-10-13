Use the theme function adapter:

```go
form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

In v2, `WithTheme` accepts a `huh.Theme`, while `ThemeCharm(true)` returns `*huh.Styles`. `ThemeFunc` wraps `ThemeCharm` so Huh can supply the boolean itself.

Bubble Tea detects the terminal background and sends a `tea.BackgroundColorMsg`. Huh stores `msg.IsDark()` and passes it to your theme function when resolving styles. If you embed the form in your own Bubble Tea model, forward that message to `form.Update`.

To force the dark variant regardless of detection:

```go
form.WithTheme(huh.ThemeFunc(func(bool) *huh.Styles {
    return huh.ThemeCharm(true)
}))
```