You do this by building the frame from layers: put your normal screen on a base layer and the dialog on a higher one, then combine them with `lipgloss.NewCompositor`. Then call `Compositor.Hit(x, y)` from the view's `OnMouse` callback. Give every layer an ID and `Hit` tells you which one is on top under the click. This includes the background, so a click outside the dialog comes back as `"base"`.

```go
type hitMsg string // ID of the layer that was clicked; "" if none

type confirmState struct {
    prompt string
    yes    bool // which button has focus; false means No (the safe default)
}

type model struct {
    width, height int
    body          string        // your existing screen, already rendered
    confirm       *confirmState // nil when no dialog is open
}

var (
    dialogStyle = lipgloss.NewStyle().
            Border(lipgloss.RoundedBorder()).
            Padding(1, 2)
    btnStyle   = lipgloss.NewStyle().Padding(0, 1)
    btnFocused = btnStyle.Reverse(true)
)

func button(label string, focused bool) string {
    if focused {
        return btnFocused.Render("[" + label + "]") // brackets and reverse video, not color alone
    }
    return btnStyle.Render(" " + label + " ")
}

func (m model) View() tea.View {
    if m.width == 0 {
        return tea.NewView("loading…")
    }

    // The base layer must be exactly the window size. A larger layer makes the frame larger.
    base := lipgloss.NewStyle().Width(m.width).Height(m.height)
    if m.confirm != nil {
        base = base.Faint(true) // extra hint only; some terminals ignore faint
    }
    layers := []*lipgloss.Layer{lipgloss.NewLayer(base.Render(m.body)).ID("base").Z(0)}
    if m.confirm != nil {
        layers = append(layers, m.dialogLayers()...)
    }

    comp := lipgloss.NewCompositor(layers...)
    v := tea.NewView(comp.Render())
    v.AltScreen = true
    v.MouseMode = tea.MouseModeCellMotion
    v.OnMouse = func(msg tea.MouseMsg) tea.Cmd {
        c, ok := msg.(tea.MouseClickMsg)
        if !ok || c.Button != tea.MouseLeft {
            return nil
        }
        id := comp.Hit(c.X, c.Y).ID() // top-most layer that has an ID
        return func() tea.Msg { return hitMsg(id) }
    }
    return v
}

func (m model) dialogLayers() []*lipgloss.Layer {
    // 60% of the width, between 30 and 60 columns, and never wider than the terminal
    w := min(max(m.width*6/10, 30), 60, m.width)
    inner := w - dialogStyle.GetHorizontalFrameSize() // v2: Width includes border and padding

    no, yes := button("No", !m.confirm.yes), button("Yes", m.confirm.yes)
    buttons := lipgloss.JoinHorizontal(lipgloss.Top, no, "  ", yes)
    content := lipgloss.JoinVertical(lipgloss.Left,
        lipgloss.NewStyle().Width(inner).Render(m.confirm.prompt),
        "",
        lipgloss.PlaceHorizontal(inner, lipgloss.Right, buttons),
    )
    box := dialogStyle.Width(w).Render(content) // padding fills the cells behind the box

    x := (m.width - lipgloss.Width(box)) / 2
    y := max((m.height-lipgloss.Height(box))/2-1, 0) // centered, one row higher

    // Find where the buttons are, so each one can be its own clickable layer
    by := y + lipgloss.Height(box) - 1 - dialogStyle.GetBorderBottomSize() - dialogStyle.GetPaddingBottom()
    bx := x + dialogStyle.GetBorderLeftSize() + dialogStyle.GetPaddingLeft() + inner - lipgloss.Width(buttons)

    return []*lipgloss.Layer{
        lipgloss.NewLayer(box).ID("dialog").X(x).Y(y).Z(1),
        lipgloss.NewLayer(no).ID("no").X(bx).Y(by).Z(2),
        lipgloss.NewLayer(yes).ID("yes").X(bx + lipgloss.Width(no) + 2).Y(by).Z(2),
    }
}
```

`Update` handles both mouse and keyboard input:

```go
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height

    case hitMsg:
        if m.confirm == nil {
            return m, nil // normal click handling for your app goes here
        }
        switch msg {
        case "yes":
            return m.resolve(true)
        case "no", "base": // a click on the background cancels; it never confirms
            return m.resolve(false)
        case "dialog":
            // click inside the dialog but not on a button: ignore it
        }

    case tea.KeyPressMsg:
        if m.confirm != nil { // the dialog keeps focus until it closes
            switch msg.String() {
            case "y":
                return m.resolve(true)
            case "n", "esc":
                return m.resolve(false)
            case "enter":
                return m.resolve(m.confirm.yes)
            case "tab", "shift+tab", "left", "right", "h", "l":
                m.confirm.yes = !m.confirm.yes
            case "ctrl+c":
                return m, tea.Quit
            }
            return m, nil
        }
        // ...your normal key handling
    }
    return m, nil
}

func (m model) resolve(ok bool) (tea.Model, tea.Cmd) {
    m.confirm = nil
    if ok {
        return m, doTheThing // the real action runs as a tea.Cmd, never inside Update
    }
    return m, nil
}
```

## Things that will break this

- **Give every layer you want to detect an ID, including the base.** `Hit` ignores layers without an ID. If the base had none, a background click would return `""`. With the ID, you get `"base"`, so you can tell "missed the dialog" apart from "hit nothing".
- **Use a different `Z` for each layer.** Two layers with the same Z have no defined order. `Z` is also compared exactly as written. It is not added to the parent's Z, even though the doc comment suggests it is.
- **Handle clicks in one place only.** `OnMouse` checks against the frame that was last drawn, which is why its closure can use the `comp` built in that `View`. But `Update` still receives the raw `tea.MouseClickMsg` as well. If you act on that too, every click is handled twice. The code above ignores the raw message and only acts on `hitMsg`.
- **Size the base layer to the window.** If a layer sticks out past the edge, the frame gets bigger. That's why the dialog width is limited to `m.width`.
- **Width math is different in v2.** In Lipgloss v2, `Width` already includes the border and padding. Code carried over from v1 such as `Width(w-2)` will make the dialog 2 columns too narrow.
- **Faint may not survive your content's own styles.** If your base content has its own ANSI styles, their reset codes can turn faint off partway through a line. That's acceptable because the dimming is only an extra hint. The border, the bracketed focused button, and the keys are what make it clear you're in a dialog, even with `NO_COLOR` or no faint support.

## Design choices

- **Every action works from the keyboard.** The mouse is a shortcut, not the only way: `y`/`n`, `Enter`, `Esc`, and `Tab` all work.
- **Default to No.** Pressing `Enter` on a fresh dialog should never run the destructive action.
- **A background click cancels, because cancel is the safe result.** If the action is truly dangerous, you could instead ignore background clicks so the user has to make an explicit choice.
- **Narrow terminals:** at 80×24 the dialog is 48 columns wide. In a 60-column tmux split it hits the 30-column minimum. Below 30 columns it fills the whole width, so the button-position math still works.
- **Test without a terminal:** check `Update` directly by sending it `hitMsg("base")`, `hitMsg("yes")`, and key presses. Then compare the rendered output against saved snapshots at 80×24 and 60×24.
