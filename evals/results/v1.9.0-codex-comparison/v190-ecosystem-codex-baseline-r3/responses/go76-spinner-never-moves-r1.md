Creating the components doesn’t start their clocks. Return their startup commands from `Init`:

```go
func (m model) Init() tea.Cmd {
    return tea.Batch(
        m.spinner.Tick, // Method value; don't call it here.
        m.timer.Init(),
    )
}
```

Also forward messages to both components in your model’s `Update`, and return their commands so ticking continues:

```go
var spinnerCmd, timerCmd tea.Cmd
m.spinner, spinnerCmd = m.spinner.Update(msg)
m.timer, timerCmd = m.timer.Update(msg)

return m, tea.Batch(spinnerCmd, timerCmd)
```

Keep your existing message handling, but ensure early returns don’t discard tick messages or the commands these components produce. `View()` only renders the current state; it doesn’t advance either component.