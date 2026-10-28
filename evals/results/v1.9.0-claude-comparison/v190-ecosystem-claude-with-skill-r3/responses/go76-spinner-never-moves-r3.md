Both components only move when they get tick messages, and nothing sends them because your `Init` returns `nil`. You need to do two things: start the ticks in `Init`, then pass each tick back to its component in `Update` and return the command it gives you.

### 1. Start the ticks in `Init`

```go
func (m model) Init() tea.Cmd {
    return tea.Batch(
        m.spinner.Tick,  // spinner has no Init(); the method value is the Cmd
        m.timer.Init(),  // timer (and stopwatch) do have Init(), which starts them
    )
}
```

Write `m.spinner.Tick` without parentheses. You're returning the method itself as the command, not calling it.

### 2. Forward the messages in `Update` and keep the returned Cmds

```go
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmds []tea.Cmd

    switch msg := msg.(type) {
    case tea.KeyPressMsg:
        if msg.String() == "ctrl+c" {
            return m, tea.Quit
        }

    case spinner.TickMsg:
        var cmd tea.Cmd
        m.spinner, cmd = m.spinner.Update(msg)
        cmds = append(cmds, cmd) // drop this and the spinner freezes after one frame

    case timer.TickMsg, timer.StartStopMsg:
        var cmd tea.Cmd
        m.timer, cmd = m.timer.Update(msg)
        cmds = append(cmds, cmd) // drop this and the timer stops counting

    case timer.TimeoutMsg:
        // countdown hit zero: do whatever "done" means for you
    }

    return m, tea.Batch(cmds...)
}
```

Each component's `Update` returns the command that schedules its next tick. If you throw that command away (`m.spinner, _ = ...`) or never forward the message, the component stops after one frame. That's the same frozen behavior you see now.

### Things that cause the same symptom
- **Not assigning the result:** `m.spinner.Update(msg)` without `m.spinner, cmd = ...` changes a copy, because models are values.
- **Returning early:** a `return m, nil` higher up in `Update` (for example in a key handler that catches every message) can swallow tick messages before they reach these cases.
- **Several timers:** each one checks its own ID and ignores ticks meant for others. Forward to all of them and they'll each pick their own.

In `View`, keep rendering `m.spinner.View()` and `m.timer.View()` as you do now. Wrap them with `tea.NewView(...)` because v2's `View` returns a `tea.View`.
