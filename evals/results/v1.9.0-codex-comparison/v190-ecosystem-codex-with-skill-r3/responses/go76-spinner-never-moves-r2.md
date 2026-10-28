Construction initializes their state; it doesn’t start their ticks. Start both in `Init`, then forward messages to both children and return their commands:

```go
func (m model) Init() tea.Cmd {
    return tea.Batch(m.spinner.Tick, m.timer.Init())
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Handle global keys here, if needed.

    var spinnerCmd, timerCmd tea.Cmd
    m.spinner, spinnerCmd = m.spinner.Update(msg)
    m.timer, timerCmd = m.timer.Update(msg)

    return m, tea.Batch(spinnerCmd, timerCmd)
}

func (m model) View() tea.View {
    return tea.NewView(m.spinner.View() + "\n" + m.timer.View())
}
```

Use `m.spinner.Tick` **without parentheses**: that method value is the command. The timer uses `m.timer.Init()` to produce its command.

Keep the updated child models and both returned commands on every update. Dropping a tick command breaks that component’s tick chain. Use matching v2 imports: `charm.land/bubbletea/v2` and `charm.land/bubbles/v2/...`.