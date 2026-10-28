Forward messages to the form, retain its returned model, and return its command so focus, validation, and cursor updates keep running.

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/huh/v2"
)

func (m model) Init() tea.Cmd {
    return tea.Batch(m.form.Init(), tea.RequestBackgroundColor)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    updated, cmd := m.form.Update(msg)
    if form, ok := updated.(*huh.Form); ok {
        m.form = form
    }

    switch m.form.State {
    case huh.StateCompleted, huh.StateAborted:
        // Or transition to another screen here.
        return m, tea.Batch(cmd, tea.Quit)
    }

    return m, cmd
}

func (m model) View() tea.View {
    return tea.NewView(m.form.View())
}
```

Huh v2’s `Update` returns a `huh.Model`, so you need the type assertion before assigning it to your `*huh.Form` field. Its `View()` returns a string; your Bubble Tea v2 parent wraps that in `tea.View`.

Forward all messages, including background-color replies and cursor ticks. Avoid consuming ordinary keys such as `q` in the parent while the user is typing.