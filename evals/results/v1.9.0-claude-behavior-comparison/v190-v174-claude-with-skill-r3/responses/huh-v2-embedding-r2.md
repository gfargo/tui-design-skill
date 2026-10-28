Forward every message to the form, not just key presses, and assign the result back to `m.form`. When `m.form.State` changes, take control back in the parent.

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/huh/v2"
)

type model struct {
    form   *huh.Form
    result string
}

func newModel() model {
    return model{
        form: huh.NewForm(
            huh.NewGroup(
                huh.NewInput().Key("name").Title("What's your name?"),
                huh.NewConfirm().Key("ok").Title("Submit?"),
            ),
        ),
    }
}

func (m model) Init() tea.Cmd {
    // huh v2 never asks for the background color itself, so the parent does.
    // The reply comes back through Update and gets forwarded to the form.
    return tea.Batch(m.form.Init(), tea.RequestBackgroundColor)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Keys the parent always owns. Handle these first, and don't take keys
    // the form needs for typing.
    if k, ok := msg.(tea.KeyPressMsg); ok && k.String() == "ctrl+c" {
        return m, tea.Interrupt
    }

    var cmds []tea.Cmd

    if m.form.State == huh.StateNormal {
        f, cmd := m.form.Update(msg) // returns (huh.Model, tea.Cmd)
        if ff, ok := f.(*huh.Form); ok {
            m.form = ff
        }
        cmds = append(cmds, cmd)
    }

    switch m.form.State {
    case huh.StateCompleted:
        m.result = m.form.GetString("name")
        // move to the next screen, start work, etc.
    case huh.StateAborted:
        return m, tea.Quit // or go back to the previous screen
    }

    return m, tea.Batch(cmds...)
}

func (m model) View() tea.View {
    var s string
    if m.form.State == huh.StateCompleted {
        s = "Hello, " + m.result + "\n"
    } else {
        s = m.form.View() // Form.View() returns a string
    }
    v := tea.NewView(s)
    // v.AltScreen = true // only if this is a full-screen app
    return v
}
```

**Why it's written this way:**

- **Forward everything.** The form needs the messages it creates internally (moving between fields, cursor blink), plus `tea.WindowSizeMsg` and `tea.BackgroundColorMsg`. If you only forward key presses, the form stops working partway through.
- **Assign the result back.** `(*huh.Form).Update` returns the `huh.Model` interface, so cast it back to `*huh.Form` and store it in `m.form`.
- **Call `m.form.Init()` from your `Init`.** It starts the form, including focusing the first field.
- **Wrap the view yourself.** `Form.View()` returns a plain string, so the parent turns it into a `tea.View`. That's also where you set `AltScreen` and other screen settings. Don't use `form.WithViewHook` here; that's for when you run the form on its own with `form.Run()`.
- **Watch `m.form.State`.** `huh.StateCompleted` and `huh.StateAborted` are your cue to take control back. After that, stop forwarding messages to the form.
- **Read answers with `.Key(...)` and `GetString`/`GetBool`, not `.Value(&m.field)`.** Your model is passed around by value, so a pointer to `m.field` taken in the constructor points at an old copy. The form would write into that copy and your model would never see the answer. If you want `.Value(...)`, point it at something on the heap, such as a `*formData` stored on the model.
- **Dark backgrounds need the `tea.RequestBackgroundColor` line.** Without it, huh v2 always draws its light theme. Because the reply passes through `Update` like any other message, the forwarding above delivers it to the form.

**Testing:** you can test this without a terminal. Send synthetic `tea.KeyPressMsg` values to `Update`, follow up with any commands it returns, and check `m.form.State` and the values you read out.
