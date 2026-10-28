Creating the components doesn’t start their ticks. Start both in `Init`, then forward messages to their `Update` methods and return the commands they produce:

```go
func (m model) Init() tea.Cmd {
	return tea.Batch(
		m.spinner.Tick, // method value—no parentheses
		m.timer.Init(),
	)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	// Handle your app's keys and other messages here.

	var spinnerCmd, timerCmd tea.Cmd
	m.spinner, spinnerCmd = m.spinner.Update(msg)
	m.timer, timerCmd = m.timer.Update(msg)

	return m, tea.Batch(spinnerCmd, timerCmd)
}
```

`View()` only renders the current state. The initial commands start ticking; forwarding messages and returning subsequent commands keeps both components running. Make sure any early returns in your existing `Update` don’t swallow their tick messages.