Both components need startup commands and must receive messages in your model’s `Update`. Rendering `View()` alone doesn’t advance them.

Start them in `Init`:

```go
func (m Model) Init() tea.Cmd {
	return tea.Batch(
		m.spinner.Tick,
		m.timer.Init(),
	)
}
```

Then forward messages to both components and return their commands:

```go
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	// Handle your app's messages here.

	var spinnerCmd, timerCmd tea.Cmd
	m.spinner, spinnerCmd = m.spinner.Update(msg)
	m.timer, timerCmd = m.timer.Update(msg)

	return m, tea.Batch(spinnerCmd, timerCmd)
}
```

The startup commands trigger the first ticks; the commands returned by each component’s `Update` schedule subsequent ticks. Preserve both the updated component models and their commands, and avoid early returns that swallow their tick messages.