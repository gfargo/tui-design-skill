In Huh v2 the built-in themes are plain functions with the signature `func(isDark bool) *huh.Styles`. `WithTheme` expects a `huh.Theme`, and a `*huh.Styles` isn't one. Calling `huh.ThemeCharm(true)` gives you a `*Styles`, which is why it no longer compiles. Wrap the function with `huh.ThemeFunc`:

```go
form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))
```

Huh's own upgrade guide shows `.WithTheme(huh.ThemeCharm(isDark))`. That doesn't compile against v2.0.3 either, so don't copy it.

## How the form learns whether the background is dark

Huh fills in `isDark` itself when a `tea.BackgroundColorMsg` arrives. But as of v2.0.3 it never sends the request for that message. What you need to do depends on how you run the form.

**1. Standalone `form.Run()`:** No parent program asks for the background color, so the reply never comes and you always get the **light** variant ([huh#834](https://github.com/charmbracelet/huh/issues/834)). Check the background yourself before the form starts, then fix the variant:

```go
isDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)

form := huh.NewForm(/* groups */).
    WithTheme(huh.ThemeFunc(func(bool) *huh.Styles {
        return huh.ThemeCharm(isDark)
    }))

err := form.Run()
```

It's safe to call `HasDarkBackground` here because no Bubble Tea program is running yet. Once one is running, the query would compete with Bubble Tea for terminal input.

**2. Form embedded in your own Bubble Tea v2 model:** Request the background color from your `Init` and pass the reply on to the form. Use the plain `huh.ThemeFunc(huh.ThemeCharm)`, and Huh picks the variant from the message:

```go
func (m model) Init() tea.Cmd {
    return tea.Batch(m.form.Init(), tea.RequestBackgroundColor)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // tea.BackgroundColorMsg falls through to here, so the form receives it
    f, cmd := m.form.Update(msg)
    if f, ok := f.(*huh.Form); ok {
        m.form = f
    }
    return m, cmd
}
```

The form renders the light variant until the reply arrives, and the reply might never come. Some terminals don't answer the OSC 11 query, and since Bubble Tea v2.0.10, `tea.WithInput(nil)` skips terminal queries entirely. Make sure the light variant looks acceptable on its own.

Source: the skill's `references/ecosystem-go.md` (Huh section, line 264, and the Lipgloss light/dark notes at lines 170–177). I didn't compile these snippets against a Go module here.
