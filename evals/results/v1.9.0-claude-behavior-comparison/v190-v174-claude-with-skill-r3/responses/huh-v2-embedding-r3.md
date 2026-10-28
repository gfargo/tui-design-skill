Send **every** message to the form, not only key presses. huh moves between fields, validates and blinks the cursor using its own internal messages. If you only pass it `tea.KeyPressMsg`, it will look like it works and then freeze on the next field.

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/huh/v2"
)

type model struct {
    form *huh.Form
    name string // bound via huh.NewInput().Value(&m.name) — use a pointer that outlives copies
    done bool
}

func (m model) Init() tea.Cmd {
    // huh v2 picks dark/light from tea.BackgroundColorMsg but never asks for one itself,
    // so the parent has to request it (and the reply gets forwarded below).
    return tea.Batch(m.form.Init(), tea.RequestBackgroundColor)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Parent-level keys first; keep this list tiny so you don't steal text entry.
    if k, ok := msg.(tea.KeyPressMsg); ok && k.String() == "ctrl+c" {
        return m, tea.Interrupt
    }

    if m.done {
        // Form is finished — handle your post-form screen here.
        return m, nil
    }

    // Forward everything: keys, WindowSizeMsg, BackgroundColorMsg, huh's internal msgs.
    f, cmd := m.form.Update(msg)
    if ff, ok := f.(*huh.Form); ok { // Update returns huh.Model, not *huh.Form
        m.form = ff
    }

    switch m.form.State {
    case huh.StateCompleted:
        m.done = true
        // read bound values / m.form.GetString("key") here, or return a Cmd that acts on them
        return m, tea.Batch(cmd, tea.Quit) // or transition to the next screen instead of quitting
    case huh.StateAborted:
        return m, tea.Quit
    }
    return m, cmd
}

func (m model) View() tea.View {
    var v tea.View
    if m.done {
        v = tea.NewView("Thanks, " + m.name + "\n")
    } else {
        v = tea.NewView(m.form.View()) // Form.View() returns a string; you wrap it
    }
    // v.AltScreen = true // only if this is a full-screen app; inline suits a bounded form
    return v
}
```

**Common mistakes:**

1. **Type assertion.** In v2, `(*huh.Form).Update` returns `(huh.Model, tea.Cmd)`. You have to assert it back to `*huh.Form`. If you skip that, `m.form` keeps the old form.
2. **Not returning `cmd`.** That `cmd` is how the form gets to its next field or group. If you drop it, the form stops responding.
3. **Calling `m.form.Init()` in your `Init`.** Without it, the first field never gets focus.
4. **Requesting the background color.** If you don't return `tea.RequestBackgroundColor` from your `Init` and forward the reply, a themed form always renders the light variant. To choose a theme, use `form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))`. The `.WithTheme(huh.ThemeCharm(isDark))` call shown in the upgrade guide doesn't compile against v2.0.3.
5. **Ending on `State`, not on a key.** Check `huh.StateCompleted` or `huh.StateAborted` after every update. Don't watch for Enter or Esc yourself.
6. **Value pointers.** Bubble Tea passes your model by value, so `.Value(&m.name)` taken from a copy will point at memory you never read again. Bind to variables that stay put, such as fields of a struct you hold by pointer or variables in the scope where you build the form. You can also skip pointers: give each field a `.Key("name")` and read it with `m.form.GetString("name")`.
7. **Window size.** Forwarding `tea.WindowSizeMsg` lets the form handle its own width. If it sits next to other content, cap it with `form.WithWidth(n)` so it fits its pane.

**Two more points:**
- **Full screen.** `tea.WithAltScreen()` is gone in v2. Set `v.AltScreen = true` on your own `tea.View` as shown above. (`form.WithViewHook` only applies when you call `form.Run()` on its own.) A bounded form usually reads better inline.
- **Accessibility.** Give users a switch, such as an `ACCESSIBLE` env var, that skips your embedded model and runs `form.WithAccessible(true).Run()` instead. That mode asks each question as a plain line-by-line prompt, which works better for screen-reader users.

**Testing:** to unit-test this, send `tea.KeyPressMsg{Code: tea.KeyEnter}` or rune literals into `Update`. Run the commands it returns until `m.form.State` changes, because huh moves between fields through those commands.
