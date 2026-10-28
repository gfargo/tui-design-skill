Forward messages to the form’s `Update`, save the returned form, and return its command. If the form fills your view, delegate `View` directly:

```go
func (m model) Init() tea.Cmd {
	return m.form.Init()
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	updated, cmd := m.form.Update(msg)
	if form, ok := updated.(*huh.Form); ok {
		m.form = form
	}
	return m, cmd
}

func (m model) View() tea.View {
	return m.form.View()
}
```

With v2, use `charm.land/bubbletea/v2` and `charm.land/huh/v2`. Bubble Tea v2’s `View` returns `tea.View`, rather than a string.

If you add your own message handling, let messages fall through to the form unless you intentionally consume them. Return the form’s command so its focus, validation, and other asynchronous behavior can run.