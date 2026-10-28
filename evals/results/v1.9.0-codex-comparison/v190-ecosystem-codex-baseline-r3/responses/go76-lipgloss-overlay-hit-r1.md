Use Lipgloss v2’s **`Layer` and `Compositor`** APIs. Give the dialog a higher Z index, center it using its rendered size, and call `Compositor.Hit(x, y)` to identify the topmost layer under a click.

Here’s a complete Bubble Tea v2 example:

```go
package main

import (
	"log"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

type model struct {
	width, height int
	showDialog    bool
	status        string
}

func (m model) Init() tea.Cmd { return nil }

// Use the same layout for rendering and hit testing.
func (m model) scene() *lipgloss.Compositor {
	background := lipgloss.NewStyle().
		Width(m.width).
		Height(m.height).
		Render("Press d to open the dialog.\n\n" + m.status)

	layers := []*lipgloss.Layer{
		lipgloss.NewLayer(background).ID("background").Z(0),
	}

	if m.showDialog {
		dialog := lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			Padding(1, 3).
			Render("Delete this item?\n\n[y] Yes    [n / Esc] Cancel")

		// Measure terminal cells, including border and padding.
		x := max(0, (m.width-lipgloss.Width(dialog))/2)
		y := max(0, (m.height-lipgloss.Height(dialog))/2)

		layers = append(layers,
			lipgloss.NewLayer(dialog).
				ID("dialog").
				X(x).Y(y).Z(1),
		)
	}

	return lipgloss.NewCompositor(layers...)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height

	case tea.KeyPressMsg:
		if msg.String() == "ctrl+c" {
			return m, tea.Quit
		}

		if m.showDialog {
			switch msg.String() {
			case "y":
				m.showDialog = false
				m.status = "Confirmed."
			case "n", "esc":
				m.showDialog = false
				m.status = "Cancelled."
			}
			return m, nil // Consume keys while the modal is open.
		}

		if msg.String() == "d" {
			m.showDialog = true
		}

	case tea.MouseClickMsg:
		if msg.Button != tea.MouseLeft {
			return m, nil
		}

		hit := m.scene().Hit(msg.X, msg.Y)

		if m.showDialog {
			switch hit.ID() {
			case "dialog":
				m.status = "Clicked inside the dialog."
			case "background":
				m.status = "Clicked outside; cancelled."
				m.showDialog = false
			}
			return m, nil // Prevent clicks reaching background controls.
		}

		// Handle ordinary background clicks here.
	}

	return m, nil
}

func (m model) View() tea.View {
	v := tea.NewView(m.scene().Render())
	v.AltScreen = true
	v.MouseMode = tea.MouseModeCellMotion
	return v
}

func main() {
	if _, err := tea.NewProgram(model{}).Run(); err != nil {
		log.Fatal(err)
	}
}
```

A few details matter:

- **Assign IDs:** `Hit` ignores layers with empty IDs.
- **Hits are rectangular:** the dialog’s border, padding, and blank cells count as inside. `hit.Empty()` means no named layer was hit.
- **Coordinates are zero-based terminal cells.** Using the alternate screen and rendering the compositor at `(0, 0)` keeps them aligned.
- Rebuilding the compositor keeps geometry current. If you retain one and change layer positions or contents, call `Refresh()` before rendering or hit testing.

For clickable Yes/Cancel buttons, give each button its own named layer above the dialog and handle those IDs too.