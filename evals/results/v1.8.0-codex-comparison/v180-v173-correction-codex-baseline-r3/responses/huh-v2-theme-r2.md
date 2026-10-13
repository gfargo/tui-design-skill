Pass the theme function itself, without calling it:

```go
form.WithTheme(huh.ThemeCharm)
```

In Huh v2, `WithTheme` takes a theme function (`func(isDark bool) *huh.Theme`). The form supplies the boolean.

During initialization, the form requests the terminal’s background color through Bubble Tea. When it receives a `tea.BackgroundColorMsg`, it uses `msg.IsDark()` to select the theme’s colors. If you embed the form in another Bubble Tea model, make sure you forward that message to the form’s `Update`.

To force dark colors regardless of detection:

```go
form.WithTheme(func(bool) *huh.Theme {
    return huh.ThemeCharm(true)
})
```