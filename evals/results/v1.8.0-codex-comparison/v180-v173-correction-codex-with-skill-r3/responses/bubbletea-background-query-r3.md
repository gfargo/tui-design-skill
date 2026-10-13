Use Bubble Tea’s background query: return `tea.RequestBackgroundColor` from `Init`, then handle `tea.BackgroundColorMsg` in `Update`.

`lipgloss.HasDarkBackground` performs terminal I/O. Inside a running Bubble Tea program it can block `Update` and compete with Bubble Tea for input. Moving it into a custom command still leaves that input conflict.

```go
func (m model) Init() tea.Cmd {
    return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.BackgroundColorMsg:
        lightDark := lipgloss.LightDark(msg.IsDark())
        m.textStyle = lipgloss.NewStyle().Foreground(
            lightDark(
                lipgloss.Color("#223344"), // light background
                lipgloss.Color("#CCDDEE"), // dark background
            ),
        )
        // Rebuild other theme-dependent styles here.
    }
    return m, nil
}
```

Initialize your model with a usable default palette and render immediately. The reply may never arrive—some terminals don’t answer OSC 11, and `tea.WithInput(nil)` disables terminal queries.

Use `HasDarkBackground` only before `Program.Run()` or in standalone code where Bubble Tea isn’t managing terminal input.