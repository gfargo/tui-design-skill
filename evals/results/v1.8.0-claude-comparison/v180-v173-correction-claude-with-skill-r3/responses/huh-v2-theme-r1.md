In Huh v2 the built-in themes changed type. `huh.ThemeCharm` is now `func(isDark bool) *huh.Styles`, so `huh.ThemeCharm(true)` gives you a `*Styles`, and `WithTheme` doesn't accept that. Wrap the function with `huh.ThemeFunc` instead:

```go
form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

Huh's own upgrade guide shows `.WithTheme(huh.ThemeCharm(isDark))`. That doesn't compile against v2.0.3, for the reason above, so don't copy it.

## How the form finds out the background is dark

Huh calls your theme function with `isDark` taken from the `tea.BackgroundColorMsg` it receives. In v2.0.3, though, Huh never sends the request that produces that message ([huh#834](https://github.com/charmbracelet/huh/issues/834)). Whether you get the right variant depends on how you run the form.

**Embedded in your own Bubble Tea model:** your parent model has to ask for the background colour and pass the reply on to the form:

```go
func (m model) Init() tea.Cmd {
    return tea.Batch(m.form.Init(), tea.RequestBackgroundColor)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Forward every message, including tea.BackgroundColorMsg, to the form.
    f, cmd := m.form.Update(msg)
    if ff, ok := f.(*huh.Form); ok {
        m.form = ff
    }
    return m, cmd
}
```

With that in place, `huh.ThemeFunc(huh.ThemeCharm)` picks the correct variant by itself.

**Standalone `form.Run()`:** there's no parent to make the request, so the form always renders the light variant. Check the background yourself before starting the form, then fix the variant:

```go
isDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)

err := huh.NewForm(/* groups */).
    WithTheme(huh.ThemeFunc(func(bool) *huh.Styles {
        return huh.ThemeCharm(isDark)
    })).
    Run()
```

Calling `lipgloss.HasDarkBackground` is safe at this point because no Bubble Tea program is reading the terminal yet. Don't call it from inside a running program, where it would compete with Bubble Tea for terminal input. Inside a program, use the `tea.RequestBackgroundColor` approach above.

This comes from the skill's Go ecosystem reference (`references/ecosystem-go.md`, Huh section), which is written against Huh v2.0.3. If you're on a newer release, check the linked issue: if it's been fixed, the plain `huh.ThemeFunc(huh.ThemeCharm)` call may be enough for standalone forms too.
