Don't call `lipgloss.HasDarkBackground` while the program is running. It writes an OSC 11 query to the terminal and then reads the reply from stdin. Bubble Tea is already reading stdin, so the two readers race. Some of your keystrokes get swallowed or delayed, which is the stutter you're seeing. Doing this inside `Update` also blocks the event loop on terminal I/O, and it re-queries on every call.

Instead, ask Bubble Tea to do the query once and handle the reply as a message:

```go
type model struct {
    styles styles
    // ...
}

func newModel() model {
    // Start with a default palette so the first frame looks right
    // even if the terminal never answers.
    return model{styles: newStyles(true)}
}

func (m model) Init() tea.Cmd {
    return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.BackgroundColorMsg:
        m.styles = newStyles(msg.IsDark())
        return m, nil
    // ...
    }
    return m, nil
}

func newStyles(isDark bool) styles {
    lightDark := lipgloss.LightDark(isDark)
    return styles{
        title: lipgloss.NewStyle().
            Foreground(lightDark(lipgloss.Color("#236"), lipgloss.Color("#cef"))),
        // ...
    }
}
```

A few details:

- **Treat the reply as an upgrade, not a requirement.** It may never arrive. Some terminals don't answer OSC 11, and since Bubble Tea v2.0.10, running with `tea.WithInput(nil)` skips terminal queries entirely. So always render with a sensible default palette first.
- **Build styles when the reply arrives, not in `View`.** Store them on the model and rebuild only when a `BackgroundColorMsg` comes in.
- **`HasDarkBackground` is still fine outside the program.** For example, a one-shot CLI that never starts Bubble Tea can call it once at startup.
- **Avoid `AdaptiveColor` in new code.** In Lip Gloss v2 it only exists in the `compat` package, for migrations. Use `LightDark`.
