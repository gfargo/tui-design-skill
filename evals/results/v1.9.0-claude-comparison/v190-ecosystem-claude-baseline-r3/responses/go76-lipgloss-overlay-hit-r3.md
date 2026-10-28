Lipgloss v2 has a layer compositor that does both jobs. You stack the dialog layer on top of your normal screen, and the same compositor tells you which layer is under a given cell. If you build the layer stack in one helper and call it from both `View` and `Update`, the hit-test always uses the same positions as the screen you drew.

```go
package main

import (
	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

type model struct {
	width, height int
	showDialog    bool
	status        string
}

var dialogStyle = lipgloss.NewStyle().
	Border(lipgloss.RoundedBorder()).
	BorderForeground(lipgloss.Color("205")).
	Padding(1, 3)

func (m model) Init() tea.Cmd { return nil }

// Your normal screen. Fill the whole window so every cell belongs to
// the background layer. Otherwise clicks on blank space hit nothing.
func (m model) background() string {
	return lipgloss.NewStyle().
		Width(m.width).
		Height(m.height).
		Render("My app\n\nPress d to delete, q to quit\n\n" + m.status)
}

func (m model) dialog() string {
	return dialogStyle.Render("Delete this file?\n\n[y] Yes    [n] No")
}

// compositor builds the layer stack. View uses it to draw and Update
// uses it to hit-test, so both see the same positions.
func (m model) compositor() *lipgloss.Compositor {
	layers := []*lipgloss.Layer{
		lipgloss.NewLayer(m.background()).ID("background"),
	}
	if m.showDialog {
		d := m.dialog()
		x := (m.width - lipgloss.Width(d)) / 2
		y := (m.height - lipgloss.Height(d)) / 2
		layers = append(layers,
			lipgloss.NewLayer(d).ID("dialog").X(x).Y(y).Z(1))
	}
	return lipgloss.NewCompositor(layers...)
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height

	case tea.KeyPressMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "d":
			m.showDialog = true
		case "y", "n", "esc":
			if m.showDialog {
				m.showDialog = false
				m.status = "answered: " + msg.String()
			}
		}

	case tea.MouseClickMsg:
		if !m.showDialog {
			break
		}
		mouse := msg.Mouse()
		hit := m.compositor().Hit(mouse.X, mouse.Y)
		switch hit.ID() {
		case "dialog":
			m.status = "clicked inside dialog"
		default: // "background", or empty
			m.showDialog = false
			m.status = "clicked outside, dismissed"
		}
	}
	return m, nil
}

func (m model) View() tea.View {
	v := tea.NewView(m.compositor().Render())
	v.AltScreen = true
	v.MouseMode = tea.MouseModeCellMotion // required to receive mouse events
	return v
}

func main() {
	tea.NewProgram(model{}).Run()
}
```

**How it works:**
- **Centering:** `(screenSize − lipgloss.Width/Height(dialog)) / 2`. Measure the dialog after rendering it, so the border and padding are included.
- **Stacking order:** the dialog gets `Z(1)` so it draws above the background. `Hit` returns the topmost layer under the given cell, so a click on the dialog reports `"dialog"`, not `"background"`.
- **Mouse input:** you only get `tea.MouseClickMsg` if you set `MouseMode` on the view. Bubble Tea v2 sets it there instead of using a program option.
- **Clickable buttons:** you can nest child layers inside the dialog, for example `lipgloss.NewLayer(d, yesBtn, noBtn)`, each with its own `ID` and an `X`/`Y` relative to the dialog. Then `hit.ID()` returns `"yes"` or `"no"` directly.

**Check your version:** the compositor API changed between the v2 betas and the final release. Earlier betas had `Canvas.Hit` returning a plain string ID, while the final release uses `Compositor` / `LayerHit`. If these names don't compile against your version, check that version's `layer.go` / `canvas.go`.

If you'd rather not use the compositor for hit-testing, you can save the dialog's `x, y, w, h` and check the click yourself: `mx >= x && mx < x+w && my >= y && my < y+h`. You'd still render with the compositor.
