Use Bubble Tea’s asynchronous background-color request. `lipgloss.HasDarkBackground` queries the terminal and waits for a response; inside `Update`, that blocks the event loop and can interfere with Bubble Tea’s input reader.

Request once in `Init`, then cache the result:

```go
func (m model) Init() tea.Cmd {
    return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.BackgroundColorMsg:
        m.isDark = msg.IsDark()
        // Rebuild your theme/styles using m.isDark.
    }

    return m, nil
}
```

Initialize your model with a usable default theme, since some terminals won’t reply. If `Init` already returns commands, combine them with `tea.Batch`.

Don’t wrap `HasDarkBackground` in a command or goroutine while Bubble Tea is running—it would still compete for terminal input. Let Bubble Tea handle the query and response.