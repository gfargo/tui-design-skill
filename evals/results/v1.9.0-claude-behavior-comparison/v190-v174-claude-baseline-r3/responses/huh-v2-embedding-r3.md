Here's the standard pattern. The thing that matters most is to forward **every** message to the form, not only key presses. The form relies on its own internal messages (focus changes, field navigation, cursor blink, window size), and if you filter those out it will look frozen.

```go
package main

import (
	tea "charm.land/bubbletea/v2"
	"charm.land/huh/v2"
)

type model struct {
	form *huh.Form
	name string
}

func newModel() model {
	m := model{}
	m.form = huh.NewForm(
		huh.NewGroup(
			huh.NewInput().Title("Name").Value(&m.name),
		),
	)
	return m
}

func (m model) Init() tea.Cmd {
	// Required: this starts the form (focuses the first field, etc.)
	return m.form.Init()
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	// Handle your own global keys first, if you have any
	if k, ok := msg.(tea.KeyPressMsg); ok {
		switch k.String() {
		case "ctrl+c":
			return m, tea.Quit
		}
	}

	var cmds []tea.Cmd

	// Forward everything to the form
	f, cmd := m.form.Update(msg)
	if f, ok := f.(*huh.Form); ok {
		m.form = f
	}
	cmds = append(cmds, cmd)

	switch m.form.State {
	case huh.StateCompleted:
		// Read results here (m.form.GetString("key") or bound vars)
		// then move to the next screen / quit / etc.
		cmds = append(cmds, tea.Quit)
	case huh.StateAborted:
		cmds = append(cmds, tea.Quit)
	}

	return m, tea.Batch(cmds...)
}

func (m model) View() tea.View {
	if m.form.State == huh.StateCompleted {
		return tea.NewView("Hello, " + m.form.GetString("name") + "!\n")
	}
	return tea.NewView(m.form.View())
}
```

Things to watch for:

1. **Return `m.form.Init()` from `Init`.** If you skip it, the first field never gets focus and the form won't respond to input.
2. **Save the updated form back to `m.form`.** `Update` gives you a new value, so you have to type-assert it to `*huh.Form` and store it. If you forget, your changes are lost.
3. **Check `m.form.State` after every update.** This is how you find out the user submitted (`StateCompleted`) or cancelled (`StateAborted`). Make sure you only act on completion once. For example, switch your model to a different screen or phase so the completion code doesn't run again on the next message.
4. **Be careful with pointers in a value receiver.** In `newModel` above, `Value(&m.name)` points at the local `m`. Bubble Tea then copies the model, so that pointer may not refer to the copy you end up reading. It's safer to give each field a `.Key("name")` and read results with `m.form.GetString("name")`, or to keep bound values behind a pointer, such as a `*formData` struct field.
5. **The form will not quit your program by itself.** When it's embedded, submitting or cancelling only changes `State`. If you want submit to trigger a command automatically, set `form.SubmitCmd` and `form.CancelCmd`.
6. **The return type of `View()` depends on your version.** I couldn't check your local module cache. If your huh v2 version's `form.View()` already returns a `tea.View` instead of a `string`, return it directly without wrapping it in `tea.NewView`. Likewise, if `form.Update` returns `*huh.Form` directly, you can drop the type assertion. The compiler will tell you which applies.

To show the form next to other UI, compose the string first, for example `lipgloss.JoinVertical(lipgloss.Left, header, m.form.View())`, and wrap the result in `tea.NewView`.
