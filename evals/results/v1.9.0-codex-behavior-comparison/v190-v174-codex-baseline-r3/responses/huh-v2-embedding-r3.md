Forward messages to the form, save the returned model, and return its command so cursor blinking, validation, and other effects keep running.

```go
func (m model) Init() tea.Cmd {
	return m.form.Init()
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	updated, cmd := m.form.Update(msg)
	if form, ok := updated.(*huh.Form); ok {
		m.form = form
	}

	if m.form.State == huh.StateCompleted {
		// Read submitted values or transition to your next screen.
	}

	return m, cmd
}

func (m model) View() tea.View {
	return m.form.View()
}
```

Use the matching v2 imports:

```go
import (
	"charm.land/bubbletea/v2"
	"charm.land/huh/v2"
)
```

Forward **all messages**, including window-size and internal messages—not just keyboard events. Also make sure your own message handling doesn’t return early before forwarding messages the form needs.