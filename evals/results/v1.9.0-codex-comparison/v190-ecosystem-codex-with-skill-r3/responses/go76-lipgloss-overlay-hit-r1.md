Use Lipgloss v2’s **layers and compositor**: put your existing screen at `Z(0)` and a centered dialog at `Z(1)`. Use the same compositor’s `Hit(x, y)` to identify what was clicked.

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/lipgloss/v2"
)

type hitMsg string

// Assumes m.width/m.height come from tea.WindowSizeMsg,
// m.body contains your existing screen, and m.confirm is a bool.
func (m model) View() tea.View {
    v := tea.NewView("")
    v.AltScreen = true
    v.MouseMode = tea.MouseModeCellMotion

    if m.width == 0 || m.height == 0 {
        return v // Waiting for the initial WindowSizeMsg.
    }

    // Keep the base within the window, including oversized content.
    base := lipgloss.NewStyle().
        Width(m.width).Height(m.height).
        MaxWidth(m.width).MaxHeight(m.height).
        Render(m.body)

    layers := []*lipgloss.Layer{
        lipgloss.NewLayer(base).ID("background").Z(0),
    }

    if m.confirm {
        if m.width < 32 || m.height < 9 {
            v.SetContent("Terminal too small.\nResize, or Esc to cancel.")
            return v
        }

        box := lipgloss.NewStyle().
            Width(min(44, m.width-4)).
            Border(lipgloss.RoundedBorder()).
            Padding(1, 2).
            Render("Delete this item?\n\ny: delete · Esc/n: cancel")

        x := (m.width - lipgloss.Width(box)) / 2
        y := (m.height - lipgloss.Height(box)) / 2

        layers = append(layers,
            lipgloss.NewLayer(box).
                ID("dialog").X(x).Y(y).Z(1),
        )
    }

    comp := lipgloss.NewCompositor(layers...)
    v.SetContent(comp.Render())

    // This closure uses the compositor for the displayed frame.
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
    if m.confirm {
        switch string(msg) {
        case "dialog":
            // Click inside the dialog, including border and padding.
            // Use separate button layers if you need button hit testing.
        case "background":
            m.confirm = false // Optional: outside click cancels.
        }
        return m, nil // Do not forward input to the underlying screen.
    }
    // Handle ordinary background clicks here.

case tea.KeyPressMsg:
    if m.confirm {
        switch msg.String() {
        case "esc", "n", "ctrl+c":
            m.confirm = false
        case "y":
            m.confirm = false
            return m, deleteItemCmd // Your asynchronous action.
        }
        return m, nil // Modal owns keyboard input.
    }
```

Key details:

- **Give both layers IDs.** `Hit` returns the topmost layer with an ID; an unidentified dialog can let hits resolve to the background.
- **Handle clicks once.** Bubble Tea also delivers raw `tea.MouseClickMsg` to `Update`; don’t perform the action there as well.
- **Measure rendered cells**, using `lipgloss.Width` and `Height`. In Lipgloss v2, style width includes padding and borders.
- Rebuild placement on resize. The example keeps one dialog border, fits both 80×24 and 60-column terminals, and shows a size fallback below 32×9.
- Clicking the dialog itself should never confirm a destructive action. Keep confirmation explicit and keyboard accessible.

`lipgloss.Place` centers content in a rectangle; the compositor is what lets you draw that rectangle **over your existing screen**.