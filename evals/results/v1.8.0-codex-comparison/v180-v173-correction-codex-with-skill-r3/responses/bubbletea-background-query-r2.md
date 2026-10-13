Use Bubble Tea’s background-color request instead. `HasDarkBackground` performs terminal I/O: inside `Update` it can block the event loop and compete with Bubble Tea for stdin, causing stutters.

Request it in `Init`, then rebuild your cached styles when the reply arrives:

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/lipgloss/v2"
)

func (m model) Init() tea.Cmd {
    return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.BackgroundColorMsg:
        lightDark := lipgloss.LightDark(msg.IsDark())
        m.titleStyle = lipgloss.NewStyle().Foreground(
            lightDark(
                lipgloss.Color("#223366"), // light background
                lipgloss.Color("#cceeff"), // dark background
            ),
        )
    }
    return m, nil
}
```

Initialize a usable default palette before running the program. Some terminals never answer the query, so rendering and input must continue without a reply. If `Init` already returns commands, combine them with `tea.Batch`.

Don’t move `HasDarkBackground` into a goroutine or `tea.Cmd` while Bubble Tea runs—it would still compete for terminal input. It’s suitable for standalone use before `Program.Run()`.