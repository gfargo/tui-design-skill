Both components animate by sending themselves tick messages. Nothing sends the first tick unless you return it from `Init`, and nothing keeps ticking unless `Update` passes each tick back to the component. You need to fix both places.

### 1. Start both components in `Init`

```go
func (m model) Init() tea.Cmd {
	return tea.Batch(
		m.spinner.Tick, // method value; already a tea.Cmd
		m.timer.Init(), // starts the countdown
	)
}
```

### 2. Pass their messages to them in `Update` and return their commands

Each `Update` call returns the command that schedules the next tick. If you drop it, the animation stops after one frame.

```go
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		if msg.String() == "q" || msg.String() == "ctrl+c" {
			return m, tea.Quit
		}

	case timer.TimeoutMsg:
		// timer hit zero: do whatever you need here
	}

	var cmd tea.Cmd
	m.spinner, cmd = m.spinner.Update(msg)
	cmds = append(cmds, cmd)

	m.timer, cmd = m.timer.Update(msg)
	cmds = append(cmds, cmd)

	return m, tea.Batch(cmds...)
}
```

### Common mistakes

- **Not assigning the result back.** `m.spinner.Update(msg)` returns an updated copy, so you need `m.spinner, cmd = ...`. Without the assignment, the frame index never moves forward.
- **Returning too early.** If one of your `case` branches returns before the components get the message, they miss `spinner.TickMsg`, `timer.TickMsg` and `timer.StartStopMsg`. Forward every message to both components, as in the code above. They check message IDs and ignore anything that isn't theirs.
- **Pointer receivers.** Use either value receivers everywhere (as above) or pointer receivers everywhere. Mixing them can silently lose your updates.
- **Calling `Tick` instead of passing it.** Pass `m.spinner.Tick` without parentheses. `m.spinner.Tick()` calls it right away and gives you a `tea.Msg`, not a command.

Your `View` can stay as it is: `m.spinner.View()` and `m.timer.View()` will show the current state once the ticks are flowing.
