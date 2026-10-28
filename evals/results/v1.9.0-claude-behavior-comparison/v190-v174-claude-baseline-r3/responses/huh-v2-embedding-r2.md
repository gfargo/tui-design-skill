Nothing in this directory or your Go module cache to check against, so this is from memory of the v2 APIs. Check the two signatures I flag below against your installed version.

```go
import (
	tea "charm.land/bubbletea/v2"
	"charm.land/huh/v2"
)

type model struct {
	form *huh.Form
}

func (m model) Init() tea.Cmd {
	return m.form.Init() // the form needs its Init cmd (focus, cursor blink, etc.)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	// Handle your own global keys first, if any
	if msg, ok := msg.(tea.KeyPressMsg); ok {
		switch msg.String() {
		case "ctrl+c":
			return m, tea.Quit
		}
	}

	var cmds []tea.Cmd

	// Send every message to the form, not just key presses
	form, cmd := m.form.Update(msg)
	if f, ok := form.(*huh.Form); ok {
		m.form = f
	}
	cmds = append(cmds, cmd)

	// React to the form finishing
	switch m.form.State {
	case huh.StateCompleted:
		// read values, e.g. m.form.GetString("name"), then move on / quit
		cmds = append(cmds, tea.Quit)
	case huh.StateAborted:
		cmds = append(cmds, tea.Quit)
	}

	return m, tea.Batch(cmds...)
}

func (m model) View() tea.View {
	var s string
	if m.form.State == huh.StateCompleted {
		s = "Done!\n"
	} else {
		s = m.form.View()
	}
	return tea.NewView(s)
}
```

Key points:

- **Send every message to the form.** That includes window size messages, blink ticks and the form's own internal messages, not just keys. If you only pass key presses through, focus changes and validation will quietly stop working.
- **Assign the result back with a type assertion.** `form.Update` returns `tea.Model`, so you need `.(*huh.Form)` before storing it in `m.form`. If you drop the result, your updates are lost.
- **Call `m.form.Init()` from your `Init`.** If the form's Init cmd never runs, the first field doesn't get focus.
- **Check `m.form.State` after updating.** This tells you when the user completed or aborted the form. Note that `form.Run()` is for standalone use only. Don't call it when the form is embedded in your model.
- **Wrap the form's output in your view.** In Bubble Tea v2, `View()` returns a `tea.View`, so you wrap the form's output with `tea.NewView(...)`. You'd also set fields like `AltScreen` on that view here, since v2 dropped the program options for them.

**Signatures to check:**
1. **The form's `View()`:** In my snippet, `m.form.View()` returns a `string`. If your huh version returns a `tea.View` instead, compose it differently, for example return it directly or use its content.
2. **The form's `Update`:** If your version's `Update` returns `*huh.Form` directly, skip the type assertion.

Running `go doc charm.land/huh/v2 Form.View` will show which version you have.
