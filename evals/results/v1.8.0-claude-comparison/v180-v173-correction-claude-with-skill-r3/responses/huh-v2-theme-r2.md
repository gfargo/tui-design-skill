**The fix:** in Huh v2, built-in themes are plain functions with the signature `func(isDark bool) *huh.Styles`. So `huh.ThemeCharm(true)` now returns a `*huh.Styles`, and `WithTheme` won't accept that because it wants a `huh.Theme`. Wrap the function with `huh.ThemeFunc` instead:

```go
form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

Note that you pass `huh.ThemeCharm` itself, without calling it. Huh's own upgrade guide shows `.WithTheme(huh.ThemeCharm(isDark))`, but that doesn't compile against v2.0.3 for the same reason.

**How the form learns the background:** Huh calls your theme function with `isDark`, which it takes from a `tea.BackgroundColorMsg`. The catch is that Huh v2.0.3 never asks the terminal for that message. Whether you get the right variant depends on how you run the form:

**1. Form embedded in your own Bubble Tea program.** The parent model has to request the background color and pass the reply on to the form:

```go
func (m model) Init() tea.Cmd {
    return tea.Batch(m.form.Init(), tea.RequestBackgroundColor)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // tea.BackgroundColorMsg falls through to the form like any other msg
    f, cmd := m.form.Update(msg)
    if f, ok := f.(*huh.Form); ok {
        m.form = f
    }
    return m, cmd
}
```

Huh shows the light variant until the reply arrives. The reply may never come: some terminals don't answer the query (OSC 11), and since Bubble Tea v2.0.10 `tea.WithInput(nil)` skips terminal queries entirely. So the light variant needs to look acceptable on its own.

**2. Standalone `form.Run()`.** There's no parent to make the request, so as written the form always renders the light variant ([huh#834](https://github.com/charmbracelet/huh/issues/834)). Check the background yourself before running the form, then fix the theme to that variant:

```go
isDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)

form := huh.NewForm(/* groups */).
    WithTheme(huh.ThemeFunc(func(bool) *huh.Styles {
        return huh.ThemeCharm(isDark)
    }))

err := form.Run()
```

Calling `HasDarkBackground` is safe here because no Bubble Tea program is reading the terminal yet. Don't call it from inside a running Bubble Tea program, where its query competes with Bubble Tea for input. In that case use approach 1.

Source: the Huh section of the skill's `references/ecosystem-go.md`, which covers Huh up to v2.0.3. If you're on a newer v2 release, check the changelog in case Huh now requests the background color itself.
