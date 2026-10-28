Start both components in `Init`, then forward messages to them and return their commands. Creating them and calling `View()` only renders their current state.

```go
func (m model) Init() tea.Cmd {
    return tea.Batch(m.spinner.Tick, m.timer.Init())
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Handle your app's messages/quit keys here.

    var spinnerCmd, timerCmd tea.Cmd
    m.spinner, spinnerCmd = m.spinner.Update(msg)
    m.timer, timerCmd = m.timer.Update(msg)

    return m, tea.Batch(spinnerCmd, timerCmd)
}

func (m model) View() tea.View {
    return tea.NewView(m.spinner.View() + " " + m.timer.View())
}
```

The details that matter:

- Spinner has no `Init()`: pass **`m.spinner.Tick`**, the command method value.
- Timer starts with **`m.timer.Init()`**.
- Keep each child’s updated model **and returned command**. Dropping the command breaks the tick chain and freezes it.

Use matching v2 imports: `charm.land/bubbletea/v2` and `charm.land/bubbles/v2/...`.