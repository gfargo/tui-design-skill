Use Lipgloss v2’s **layers and compositor**. Render your existing screen as the bottom layer, position the dialog above it, and use `Compositor.Hit(x, y)` to identify the clicked layer.

Bubble Tea v2’s `View.OnMouse` lets you hit-test against the **last rendered frame**, so resizing and clicking use the same geometry.

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/lipgloss/v2"
)

type hitMsg string

// Assumes model has width, height, body, and dialogOpen fields.
func (m model) View() tea.View {
    v := tea.NewView("")
    v.AltScreen = true
    v.MouseMode = tea.MouseModeCellMotion

    if m.width == 0 || m.height == 0 {
        return v // Wait for WindowSizeMsg.
    }

    // Keep the base exactly within the window.
    base := lipgloss.NewStyle().
        Width(m.width).Height(m.height).
        MaxWidth(m.width).MaxHeight(m.height).
        Render(m.body)

    layers := []*lipgloss.Layer{
        lipgloss.NewLayer(base).ID("background").Z(0),
    }

    if m.dialogOpen {
        if m.width < 30 || m.height < 9 {
            v.SetContent("Terminal too small. Resize or press Esc.")
            return v
        }

        box := lipgloss.NewStyle().
            Width(min(48, m.width-4)).
            Border(lipgloss.RoundedBorder()).
            Padding(1, 2).
            Render("Confirm action?\n\ny: confirm   n/Esc: cancel")

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
        // Click landed inside the dialog, including its border.
    case "background":
        if m.dialogOpen {
            // Ignore, or cancel the dialog if that is your policy.
            // Do not activate the underlying screen.
        } else {
            // Handle a normal background click.
        }
    }

case tea.KeyPressMsg:
    if m.dialogOpen {
        switch msg.String() {
        case "y":
            m.dialogOpen = false
            // Return your confirmation command here.
        case "n", "esc":
            m.dialogOpen = false
        }
        return m, nil // Trap keyboard input while the dialog is open.
    }
```

Key details:

- Give **every clickable layer an ID**. `Hit` selects the topmost identified layer; an empty ID means no hit.
- Use distinct `Z` values; equal values have no defined ordering.
- `Update` also receives raw mouse messages. Handle clicks through this `hitMsg` path once to avoid duplicate actions.
- `lipgloss.Place` alone pads content for positioning; use the compositor to preserve the existing screen underneath.
- In Lipgloss v2, `Width` includes border and padding. Measure rendered cells with `lipgloss.Width` and `Height`, never `len`.

At both 80×24 and 60 columns, this keeps one centered, bordered dialog with visible keyboard controls. Below 30×9 it shows a resize message while Esc remains available.