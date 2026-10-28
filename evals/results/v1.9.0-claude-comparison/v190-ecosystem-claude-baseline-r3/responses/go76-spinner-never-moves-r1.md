Both components are driven by tick messages. Each one only advances when it gets its own `TickMsg`, and each tick returns a command that schedules the next one. If `Init` returns `nil`, the first tick never fires. Even once it does, the components only keep going if your `Update` passes their messages back to them.

You need two changes.

### 1. Start both tick loops in `Init`

```go
func (m model) Init() tea.Cmd {
	return tea.Batch(
		m.spinner.Tick, // method value; it satisfies tea.Cmd
		m.timer.Init(), // starts the countdown
	)
}
```

### 2. Pass their messages to them in `Update` and return the commands they give back

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
		return m, cmd // this cmd schedules the next frame

	case timer.TickMsg, timer.StartStopMsg:
		var cmd tea.Cmd
		m.timer, cmd = m.timer.Update(msg)
		return m, cmd

	case timer.TimeoutMsg:
		// countdown finished; do something here or tea.Quit
	}
	return m, nil
}
```

### Common mistakes that cause the same freeze

- **Not reassigning the sub-model.** `Update` uses value receivers, so `m.spinner.Update(msg)` without `m.spinner, cmd = ...` throws away the new frame.
- **Discarding the returned cmd.** If you return `m, nil` after updating the spinner or timer, the loop stops after one tick. When several components return commands in the same branch, collect them into a slice and return `tea.Batch(cmds...)`.
- **Catching ticks too early.** A catch-all branch or an early `return` placed before these cases will swallow the ticks.
- **Copying a model to build a second one.** Every spinner and timer has an internal ID and ignores ticks carrying a different ID. If you need two of them, create each with its own `spinner.New()` / `timer.New()`.

Rendering stays as it is: call `m.spinner.View()` and `m.timer.View()` inside your `View`.
