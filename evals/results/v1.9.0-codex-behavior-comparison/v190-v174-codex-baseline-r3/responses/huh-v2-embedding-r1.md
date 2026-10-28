Forward messages to the form, keep the returned `*huh.Form`, and return its command so Bubble Tea can run it:

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
		return m, tea.Quit // Or transition to your next screen.
	}

	return m, cmd
}

func (m model) View() tea.View {
	return m.form.View()
}
```

Use the v2 imports:

```go
import (
	tea "charm.land/bubbletea/v2"
	"charm.land/huh/v2"
)
```

Forward **all messages**, including window sizes and internal form messages—not just key presses. In v2, `View()` returns `tea.View`, so you can delegate directly to the form.