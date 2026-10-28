Use Lip Gloss v2’s **layers and compositor**: render your screen as the bottom layer and the dialog as a higher layer. Give each an ID, then call `Compositor.Hit(x, y)` to identify the topmost layer under a click.

These imports use the stable v2 module paths:

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/lipgloss/v2"
)
```

Add a shared layout method to your model so rendering and hit testing use identical positions. Here, `m.screen()` represents your existing screen renderer:

```go
type model struct {
    width, height int
    confirming    bool
    status        string
}

func (m model) layout() *lipgloss.Compositor {
    // Fill the viewport so blank background cells are also clickable.
    background := lipgloss.NewStyle().
        Width(m.width).
        Height(m.height).
        Render(m.screen())

    layers := []*lipgloss.Layer{
        lipgloss.NewLayer(background).ID("background").Z(0),
    }

    if m.confirming {
        dialog := lipgloss.NewStyle().
            Border(lipgloss.RoundedBorder()).
            Padding(1, 3).
            Background(lipgloss.Color("#252535")).
            Foreground(lipgloss.Color("#FFFFFF")).
            Render("Proceed with this action?\n\n[y] Confirm    [n / Esc] Cancel")

        // Measure the rendered string: borders and padding count.
        w, h := lipgloss.Size(dialog)
        x := max(0, (m.width-w)/2)
        y := max(0, (m.height-h)/2)

        layers = append(layers,
            lipgloss.NewLayer(dialog).
                ID("dialog").
                X(x).Y(y).Z(1),
        )
    }

    return lipgloss.NewCompositor(layers...)
}

func (m model) View() tea.View {
    // A fixed canvas clips content to the terminal dimensions.
    content := lipgloss.NewCanvas(m.width, m.height).
        Compose(m.layout()).
        Render()

    v := tea.NewView(content)
    v.AltScreen = true
    v.MouseMode = tea.MouseModeCellMotion
    return v
}
```

Handle clicks in `Update`:

```go
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height

    case tea.MouseClickMsg:
        if msg.Button != tea.MouseLeft {
            return m, nil
        }

        hit := m.layout().Hit(msg.X, msg.Y)

        if m.confirming {
            switch hit.ID() {
            case "dialog":
                m.status = "Clicked inside the dialog"
            case "background":
                m.status = "Clicked outside; canceled"
                m.confirming = false
            }

            // Consume modal clicks here; don't forward them to
            // the underlying screen's controls.
            return m, nil
        }

        // Handle ordinary screen clicks here.

    case tea.KeyPressMsg:
        if m.confirming {
            switch msg.String() {
            case "y":
                m.confirming = false
                m.status = "Confirmed"
                // Return your action's command here.
            case "n", "esc":
                m.confirming = false
                m.status = "Canceled"
            }
            return m, nil
        }

        if msg.String() == "c" {
            m.confirming = true
        }
    }

    return m, nil
}
```

A few details matter:

- `Hit` returns a `LayerHit`; use `.ID()` or `.Empty()`.
- Hit testing uses **rectangular terminal-cell bounds**, including borders, padding, and spaces. Layers with empty IDs are ignored.
- `AltScreen` keeps this example’s view origin aligned with the mouse’s terminal coordinates.
- If you retain a compositor and later move its layers, call `Refresh()` before rendering or hit testing. The example rebuilds it instead.

I checked these APIs against the locally installed Bubble Tea **v2.1.0** and Lip Gloss **v2.0.6** sources.