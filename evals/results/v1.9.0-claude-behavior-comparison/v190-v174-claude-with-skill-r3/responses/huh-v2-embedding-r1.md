The form needs **every** message, not just key presses. Huh moves between fields and groups using its own internal messages. It also uses `tea.WindowSizeMsg` for sizing and `tea.BackgroundColorMsg` to choose light or dark styles. If you forward only keys, the form looks fine but won't advance.

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/huh/v2"
)

type model struct {
    form *huh.Form
    name string // copied out after completion
}

func newModel() model {
    return model{
        form: huh.NewForm(
            huh.NewGroup(
                huh.NewInput().Key("name").Title("What's your name?"),
                huh.NewConfirm().Key("ok").Title("Submit?"),
            ),
        ).WithTheme(huh.ThemeFunc(huh.ThemeCharm)),
    }
}

func (m model) Init() tea.Cmd {
    // Huh v2 picks light/dark from tea.BackgroundColorMsg but never asks for it,
    // so the parent requests it and forwards the reply.
    return tea.Batch(m.form.Init(), tea.RequestBackgroundColor)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Your own global keys go first, but don't swallow keys the form needs.
    if k, ok := msg.(tea.KeyPressMsg); ok && k.String() == "ctrl+c" {
        return m, tea.Quit
    }

    // Forward everything else. Update returns huh.Model, so assert it back.
    var cmd tea.Cmd
    f, cmd := m.form.Update(msg)
    if ff, ok := f.(*huh.Form); ok {
        m.form = ff
    }

    switch m.form.State {
    case huh.StateCompleted:
        m.name = m.form.GetString("name")
        // Switch to your next screen here, or quit:
        return m, tea.Batch(cmd, tea.Quit)
    case huh.StateAborted:
        return m, tea.Quit
    }
    return m, cmd
}

func (m model) View() tea.View {
    v := tea.NewView(m.form.View()) // form.View() is a string; wrap it
    v.AltScreen = true              // v2: set on the view, not tea.WithAltScreen()
    return v
}
```

**Things that commonly go wrong:**

- **Don't use `.Value(&m.field)` with a value-receiver model.** Bubble Tea copies `model` on every `Update`, so the pointer ends up pointing at a stale copy. Either give fields a `.Key(...)` and read them back with `m.form.GetString` / `GetBool` / `Get` (as above), or point `.Value` at a heap-allocated struct the model holds by pointer.
- **Check `m.form.State` after every forwarded message.** When the form is embedded, nothing quits for you. `form.Run()` normally does that, but here your parent decides what happens on `StateCompleted` or `StateAborted`.
- **Stop forwarding once the form is done.** If your app moves to another screen, add a `mode` field so later messages go to the new screen instead of the finished form.
- **The theme API changed in v2.** Built-in themes are now `func(isDark bool) *Styles`, so wrap them with `huh.ThemeFunc(...)`. The upgrade guide shows `.WithTheme(huh.ThemeCharm(isDark))`, but that doesn't compile against v2.0.3.
- **The form doesn't own the whole screen.** If it shares the screen with other panes, send it a resized `tea.WindowSizeMsg` (or call `m.form.WithWidth(w)`) so it lays out inside its pane.
- **Accessibility:** consider an `ACCESSIBLE` env switch that calls `form.WithAccessible(true)` and runs the form standalone. That mode skips Bubble Tea and asks plain line-by-line prompts, which screen readers handle much better.
