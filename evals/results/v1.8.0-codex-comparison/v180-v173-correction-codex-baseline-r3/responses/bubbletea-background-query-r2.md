Use Bubble Tea’s asynchronous background-color query. `lipgloss.HasDarkBackground` performs terminal I/O and can block `Update` or compete with Bubble Tea for stdin. Moving that same call into a command still risks competing reads.

Request the color in `Init`, then choose and cache your theme when the response arrives:

```go
func (m model) Init() tea.Cmd {
    return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.BackgroundColorMsg:
        if msg.IsDark() {
            m.theme = darkTheme
        } else {
            m.theme = lightTheme
        }
    }

    return m, nil
}
```

Start with a default theme so the app remains usable if the terminal doesn’t answer. Keep terminal reads under Bubble Tea’s control, and use the cached theme in `View`.