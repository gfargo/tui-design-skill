Use Bubble Tea’s background query: return `tea.RequestBackgroundColor` from `Init`, then handle `tea.BackgroundColorMsg` in `Update`.

`lipgloss.HasDarkBackground` performs terminal I/O. Inside `Update`, it blocks the event loop and competes with Bubble Tea’s input reader. Moving it into a goroutine or `tea.Cmd` still leaves competing readers.

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
        m.titleStyle = lipgloss.NewStyle().
            Foreground(lightDark(
                lipgloss.Color("#223366"), // light background
                lipgloss.Color("#CCEEFF"), // dark background
            ))
    // Keep your existing message handlers here.
    }
    return m, nil
}
```

Initialize a usable default palette **before the first render**. The response may never arrive: some terminals don’t answer background queries, and `tea.WithInput(nil)` skips terminal queries in recent v2 versions.

If `Init` already returns commands, combine them with `tea.Batch`. Reserve `HasDarkBackground` for standalone use or detection **before** `Program.Run()`.