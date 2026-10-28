`New()` creates their state; `View()` only renders it. Start their commands in `Init`, then forward messages to both children and return their next commands:

```go
func (m model) Init() tea.Cmd {
    return tea.Batch(m.spinner.Tick, m.timer.Init())
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Handle parent events here; avoid early returns that swallow ticks.

    var spinnerCmd, timerCmd tea.Cmd
    m.spinner, spinnerCmd = m.spinner.Update(msg)
    m.timer, timerCmd = m.timer.Update(msg)

    return m, tea.Batch(spinnerCmd, timerCmd)
}

func (m model) View() tea.View {
    return tea.NewView(m.spinner.View() + "\n" + m.timer.View())
}
```

The spinner uses **`m.spinner.Tick` without parentheses** as its initial command; it has no `Init()`. The timer uses **`m.timer.Init()`**.

Keep both updated child models and both returned commands. Dropping a command breaks that component’s tick chain.