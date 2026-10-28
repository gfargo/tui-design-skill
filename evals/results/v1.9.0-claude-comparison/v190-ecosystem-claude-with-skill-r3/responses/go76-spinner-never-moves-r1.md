Both components are driven by commands, and they only advance when a message comes back to them. Creating them in `New()` doesn't start anything. With `Init` returning `nil`, the first tick is never scheduled, so the spinner stays on frame 0 and the timer never counts down. There are three things to change.

**1. Start both in `Init`.** The spinner has no `Init()`. Its `Tick` method value is the command, so don't call it. The timer has an `Init()` that starts it:

```go
func (m model) Init() tea.Cmd {
    return tea.Batch(m.spinner.Tick, m.timer.Init())
}
```

**2. Send their messages back to them in `Update`, and return the commands they give you.** Each `Update` returns the command for the next tick. If you drop that command, the component stops again after one frame:

```go
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyPressMsg:
        if msg.String() == "ctrl+c" {
            return m, tea.Quit
        }

    case spinner.TickMsg:
        var cmd tea.Cmd
        m.spinner, cmd = m.spinner.Update(msg)
        return m, cmd // drop this and the spinner freezes

    case timer.TickMsg, timer.StartStopMsg:
        var cmd tea.Cmd
        m.timer, cmd = m.timer.Update(msg)
        return m, cmd // drop this and the timer stops

    case timer.TimeoutMsg:
        // countdown finished: react here (quit, show "done", etc.)
    }
    return m, nil
}
```

If your `Update` already has other cases that each return early, check that none of them catch these messages first. A catch-all `default: return m, nil` placed ahead of these cases would block them.

**3. Keep the model value you get back.** `Update` and `Init` use value receivers, so `m.spinner, cmd = m.spinner.Update(msg)` has to assign the result back to the field, and you have to return that `m`. If you call `m.spinner.Update(msg)` and throw away the returned model, the spinner never moves past its current frame.

**One more thing for v2:** bubbles still return strings from `View()`, so wrap them yourself in the parent:

```go
func (m model) View() tea.View {
    return tea.NewView(m.spinner.View() + " " + m.timer.View())
}
```

Each spinner and timer instance tags its tick messages with its own ID and ignores messages carrying a different ID. If you run several timers, send `timer.TickMsg` to all of them; each one will only accept its own.
