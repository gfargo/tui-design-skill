Use Lipgloss v2’s **layers and compositor**: put the existing screen in one layer, center the dialog in a higher layer, and call `Compositor.Hit(x, y)` to identify the topmost layer under a click.

This example uses `charm.land/bubbletea/v2` and `charm.land/lipgloss/v2`:

```go
package main

import (
	"log"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

type model struct {
	width, height int
	showConfirm   bool
	status        string
}

func (m model) Init() tea.Cmd { return nil }

// Use the same layout for rendering and hit testing.
func (m model) scene() *lipgloss.Compositor {
	background := lipgloss.NewStyle().
		Width(m.width).
		Height(m.height).
		Render("Your existing screen\n\n" + m.status)

	layers := []*lipgloss.Layer{
		lipgloss.NewLayer(background).ID("background").Z(0),
	}

	if m.showConfirm {
		dialog := lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			Padding(1, 2).
			Render("Continue?\n\n[y] Yes    [n / Esc] Cancel")

		// Measure rendered cells, including border and padding.
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
	// A fixed-size canvas clips content to the terminal.
	content := lipgloss.NewCanvas(m.width, m.height).
		Compose(m.scene()).
		Render()

	v := tea.NewView(content)
	v.AltScreen = true
	v.MouseMode = tea.MouseModeCellMotion
	return v
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height

	case tea.KeyPressMsg:
		switch msg.String() {
		case "ctrl+c":
			return m, tea.Quit
		case "y":
			if m.showConfirm {
				m.showConfirm = false
				m.status = "Confirmed"
				// Run the confirmed action here.
			}
		case "n", "esc":
			m.showConfirm = false
		case "c":
			m.showConfirm = true
		}

	case tea.MouseClickMsg:
		if msg.Button != tea.MouseLeft {
			return m, nil
		}

		hit := m.scene().Hit(msg.X, msg.Y)

		if m.showConfirm {
			switch hit.ID() {
			case "dialog":
				m.status = "Clicked inside dialog"
				// Route to dialog controls here.
			case "background":
				m.showConfirm = false // Optional: dismiss on outside click.
				m.status = "Clicked background"
			}
			// Consume the click while modal; don't forward it underneath.
			return m, nil
		}

		// Handle normal screen clicks here.
	}
	return m, nil
}

func main() {
	if _, err := tea.NewProgram(model{
		showConfirm: true,
	}).Run(); err != nil {
		log.Fatal(err)
	}
}
```

A few details matter:

- **Assign IDs to both layers.** `Hit` ignores layers with empty IDs and returns a `LayerHit`; inspect `hit.ID()` or `hit.Empty()`.
- Hit testing uses **rectangular bounds**, including dialog padding and borders. It does not test whether a particular character is visible.
- Mouse coordinates are zero-based terminal cells. With this full-screen view, they match compositor coordinates directly.
- Rebuilding the scene keeps rendering and hit testing consistent. If you retain a compositor and change layer positions, call `Refresh()`.
- For clickable Yes/Cancel buttons, give each button its own positioned layer and ID with a higher Z value; use `hit.Bounds().Min` to convert a click to local coordinates.

Verified against locally installed Bubble Tea v2.1.0 and Lipgloss v2.0.6 source.