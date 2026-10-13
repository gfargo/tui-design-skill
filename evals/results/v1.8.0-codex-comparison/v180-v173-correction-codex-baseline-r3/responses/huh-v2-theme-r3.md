Use the function wrapped in `huh.ThemeFunc`:

```go
form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

`WithTheme` expects a `huh.Theme`, which implements `Theme(isDark bool) *huh.Styles`. Calling `ThemeCharm(true)` produces `*huh.Styles`, which doesn’t implement that interface; `ThemeFunc` supplies the adapter. [Theme source](https://github.com/charmbracelet/huh/blob/main/theme.go)

Background detection comes from Bubble Tea v2’s `tea.BackgroundColorMsg`. Huh stores `msg.IsDark()` and passes that boolean into your theme function when rendering. With `form.Run()`, this happens automatically. If you embed the form in another Bubble Tea model, forward that message to `form.Update(msg)`. Until a background message arrives, the boolean defaults to `false` (light). [Form source](https://github.com/charmbracelet/huh/blob/main/form.go)

To always use dark styles:

```go
form.WithTheme(huh.ThemeFunc(func(_ bool) *huh.Styles {
    return huh.ThemeCharm(true)
}))
```