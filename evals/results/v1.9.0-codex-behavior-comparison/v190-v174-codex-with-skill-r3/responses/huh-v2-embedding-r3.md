Forward messages to the form, keep its returned command, and wrap its rendered string in `tea.NewView`. Also call the form’s `Init`:

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

`Form.Update` returns a `huh.Model`, so you need the type assertion instead of assigning directly to `m.form`. Forward **all messages**, including resize, background-color, and internal form messages; returning `cmd` keeps the form’s event loop running.

The background-color request lets huh choose its theme variant. Avoid global single-letter quit bindings such as `q` while the form accepts text.