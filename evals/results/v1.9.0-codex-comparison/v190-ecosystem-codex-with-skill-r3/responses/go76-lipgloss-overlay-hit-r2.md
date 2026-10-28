Use Lipgloss v2’s **layers and compositor**. Give the screen and dialog IDs, then call `compositor.Hit(x, y)` to identify the topmost layer under the click.

Build the compositor in `View()` and capture it in `View.OnMouse`: this hit-tests against the frame the user actually saw.

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/lipgloss/v2"
)

type hitMsg string

// Assumes model has width, height, body, and showConfirm fields.
func (m model) View() tea.View {
    v := tea.NewView("")
    v.AltScreen = true
    v.MouseMode = tea.MouseModeCellMotion

    if m.width <= 0 || m.height <= 0 {
        return v // Wait for WindowSizeMsg.
    }

    // Keep the background exactly within the terminal.
    base := lipgloss.NewStyle().
        Width(m.width).Height(m.height).
        MaxWidth(m.width).MaxHeight(m.height).
        Render(m.body)

    layers := []*lipgloss.Layer{
        lipgloss.NewLayer(base).ID("background").Z(0),
    }

    if m.showConfirm {
        if m.width < 30 || m.height < 9 {
            v.SetContent("Terminal too small.\nResize, or press Esc to cancel.")
            return v
        }

        box := lipgloss.NewStyle().
            Width(min(48, m.width-4)).
            Border(lipgloss.RoundedBorder()).
            Padding(1, 2).
            Render("Confirm action?\n\n[y] Confirm   [n / Esc] Cancel")

        // Measure rendered terminal cells, including border and padding.
        x := (m.width - lipgloss.Width(box)) / 2
        y := (m.height - lipgloss.Height(box)) / 2

        layers = append(layers,
            lipgloss.NewLayer(box).
                ID("dialog").X(x).Y(y).Z(1),
        )
    }

    comp := lipgloss.NewCompositor(layers...)
    v.SetContent(comp.Render())

    v.OnMouse = func(msg tea.MouseMsg) tea.Cmd {
        click, ok := msg.(tea.MouseClickMsg)
        if !ok || click.Button != tea.MouseLeft {
            return nil
        }

        id := comp.Hit(click.X, click.Y).ID()
        return func() tea.Msg { return hitMsg(id) }
    }

    return v
}
```

Handle the resulting message in `Update`:

```go
case tea.WindowSizeMsg:
    m.width, m.height = msg.Width, msg.Height

case hitMsg:
    switch string(msg) {
    case "dialog":
        // Inside the dialog, including its border and padding.
    case "background":
        // Outside the dialog. Ignore, or dismiss according to your UX.
    }

case tea.MouseClickMsg:
    // Already handled through OnMouse; don't process it twice.

case tea.KeyPressMsg:
    if m.showConfirm {
        switch msg.String() {
        case "y":
            m.showConfirm = false
            // Return a command that performs the confirmed action.
        case "n", "esc":
            m.showConfirm = false
        }
        return m, nil // Trap input: don't forward to background widgets.
    }
```

A few details matter:

- **ID every clickable layer.** `Hit` selects the topmost layer with an ID; an empty ID means no identified layer was hit.
- Use distinct `Z` values. The background is `0`, the dialog is `1`.
- `lipgloss.Place` centers content in a blank area; the compositor overlays it on your existing screen.
- At both 80×24 and 60 columns, this uses one centered dialog border with visible keyboard controls. Below the declared minimum, it shows a resize message.
- Detecting `"dialog"` does **not** mean “confirm.” For clickable buttons, add separately identified button layers above the dialog and route those IDs to the same actions as the keyboard.