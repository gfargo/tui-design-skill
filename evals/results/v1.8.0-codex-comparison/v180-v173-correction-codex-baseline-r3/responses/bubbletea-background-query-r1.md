Use Bubble Tea’s asynchronous background-color request. `lipgloss.HasDarkBackground` queries the terminal and reads stdin synchronously; calling it in `Update` blocks the event loop and competes with Bubble Tea’s input reader.

Request the color in `Init`, then select and cache your theme when the response arrives:

```go
func (m model) Init() tea.Cmd {
    return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.BackgroundColorMsg:
        m.styles = makeStyles(msg.IsDark())
    }

    return m, nil
}
```

If you already have initialization commands, combine them with `tea.Batch`.

Start with a default theme so the app renders even if the terminal never responds. Keep terminal reads out of `Update` and `View`; moving `HasDarkBackground` into a goroutine still risks competing for stdin.