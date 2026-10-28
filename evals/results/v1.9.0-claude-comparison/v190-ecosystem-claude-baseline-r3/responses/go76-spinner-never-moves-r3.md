Both components are driven by tick messages. Nothing animates until a command starts the first tick, and each tick message has to be passed back to the component's `Update` so it can schedule the next one. You need two changes.

### 1. Start the tick loops in `Init`

```go
func (m model) Init() tea.Cmd {
	return tea.Batch(
		m.spinner.Tick, // spinner: a func() tea.Msg, so it works as a tea.Cmd
		m.timer.Init(), // timer: starts its countdown ticks
	)
}
```

### 2. Pass their messages back in `Update` and save the returned models

```go
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		if msg.String() == "q" || msg.String() == "ctrl+c" {
			return m, tea.Quit
		}

	case spinner.TickMsg:
		var cmd tea.Cmd
		m.spinner, cmd = m.spinner.Update(msg)
		return m, cmd

	case timer.TickMsg, timer.StartStopMsg:
		var cmd tea.Cmd
		m.timer, cmd = m.timer.Update(msg)
		return m, cmd

	case timer.TimeoutMsg:
		// the countdown has finished; handle it here (quit, change state, etc.)
	}
	return m, nil
}
```

### Common mistakes
- **Not saving the returned model.** Both components are value types. If you write `m.spinner.Update(msg)` without assigning the result back to `m.spinner`, the frame never advances.
- **Not returning the `cmd`.** That command schedules the next tick. If you drop it, the spinner or timer moves once and then stops.
- **Dropping other messages.** If your `Update` returns early for every message type it doesn't handle, ticks never reach the components. A fallback that sends unhandled messages to both components is also fine, because each tick carries an ID and the component ignores ticks that aren't its own.
- **Timer interval.** Set the tick rate with `timer.New(d, timer.WithInterval(time.Second))` in v2. Use `timer.New(d)` if the default is fine.

After these two changes the spinner animates and the timer counts down.
