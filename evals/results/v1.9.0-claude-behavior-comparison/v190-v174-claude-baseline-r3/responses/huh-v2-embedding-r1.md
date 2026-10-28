I couldn't find huh in your local module cache, so this is from memory of the v2 APIs. Check the exact signatures against the version you have installed.

```go
import (
	tea "charm.land/bubbletea/v2"
	"charm.land/huh/v2"
)

type model struct {
	form *huh.Form
	// ...your other state
}

func (m model) Init() tea.Cmd {
	return m.form.Init() // the form needs its init cmd (cursor blink, focusing the first field, etc.)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	// Handle your own global keys first, if you have any
	if k, ok := msg.(tea.KeyPressMsg); ok && k.String() == "ctrl+c" {
		return m, tea.Quit
	}

	var cmds []tea.Cmd

	// Pass EVERY message to the form, not only key presses.
	// It also needs WindowSizeMsg, blink ticks and its own internal msgs.
	fm, cmd := m.form.Update(msg)
	if f, ok := fm.(*huh.Form); ok {
		m.form = f
	}
	cmds = append(cmds, cmd)

	switch m.form.State {
	case huh.StateCompleted:
		// read values, e.g. m.form.GetString("name"), or the bound vars
		// switch to the next screen, or:
		cmds = append(cmds, tea.Quit)
	case huh.StateAborted:
		cmds = append(cmds, tea.Quit)
	}

	return m, tea.Batch(cmds...)
}

func (m model) View() tea.View {
	if m.form.State == huh.StateCompleted {
		return tea.NewView("Done!\n")
	}
	return tea.NewView(m.form.View())
}
```

Things to watch for:

- **Use the form's return value.** `form.Update` returns a `tea.Model`. Type-assert it back to `*huh.Form` and store it, or the form's state won't advance.
- **Forward all messages to the form.** If you only pass it key presses, blinking cursors, field validation and resizing will break silently.
- **Call `form.Init()` in your `Init`.** If you skip it, the first field may not be focused.
- **Bubble Tea v2's `View` returns `tea.View`.** Wrap the form's string with `tea.NewView(...)`. If your huh v2 version's `form.View()` already returns `tea.View`, return it directly instead.
- **Completion doesn't quit the program on its own.** When the form is embedded, you check `m.form.State` and decide what happens next. To have the form send a specific message when it's submitted or cancelled, set `form.SubmitCmd` / `form.CancelCmd`.
- **Keep the form behind a pointer** (`*huh.Form`). That's fine even though `model` itself has a value receiver.
