Both components only move when a message loop drives them. Creating them in `New()` builds the state but sends no messages. Since your `Init` returns `nil`, no first tick is ever sent, so nothing updates.

You need to change two things.

### 1. Start them in `Init`

```go
func (m model) Init() tea.Cmd {
    return tea.Batch(
        m.spinner.Tick,  // spinner has no Init(); the Tick method value *is* the Cmd
        m.timer.Init(),  // timer (and stopwatch) do have Init(), which starts the countdown
    )
}
```

Write `m.spinner.Tick` without parentheses. It's the `tea.Cmd` itself, not something you call.

### 2. Pass their messages to them in `Update` and return the Cmds they give back

Each tick returns a Cmd that schedules the next tick. If you drop that Cmd, the component stops after one frame.

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
        cmds = append(cmds, cmd)

    case timer.TickMsg, timer.StartStopMsg:
        var cmd tea.Cmd
        m.timer, cmd = m.timer.Update(msg)
        cmds = append(cmds, cmd)

    case timer.TimeoutMsg:
        // countdown finished: react here (set state, quit, etc.)
    }

    return m, tea.Batch(cmds...)
}
```

Then render both in `View`: `m.spinner.View()` and `m.timer.View()`.

### Things to check if it still doesn't move

- **Value receivers:** `m.spinner, cmd = m.spinner.Update(msg)` must assign back to the model you return. Updating a copy and returning the old `m` freezes it.
- **An early `return` before the child update:** if a generic case (for example, a catch-all that returns `m, nil`) catches the tick first, the chain breaks.
- **Multiple spinners or timers:** each has its own ID and ignores ticks meant for the others. Forward each message to every instance, or switch on the ID. Don't assume one tick drives them all.
- **Stopping and restarting the timer:** use `m.timer.Toggle()`, `Start()` or `Stop()`, and return the Cmd they produce. Returning `nil` there causes the same freeze.

A tip from the Bubble Tea guidance in the skill: Bubbles components don't read `tea.WindowSizeMsg` on their own. If you later add a `list` or `viewport`, pass the window size to them too. Until the first size message arrives, show a placeholder like `"loading…"` from `View`.
