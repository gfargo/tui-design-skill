Lipgloss v2 can do both jobs with **layers and a compositor**. You put your normal screen on a bottom layer and the dialog on a higher layer at a centered position. The compositor draws the stack, and its `Hit(x, y)` method tells you which layer is on top at a given cell. Hit-test the same layout you render, and the click detection will always match what's on screen.

```go
package main

import (
	"fmt"
	"os"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

var dialogStyle = lipgloss.NewStyle().
	Border(lipgloss.RoundedBorder()).
	BorderForeground(lipgloss.Color("63")).
	Padding(1, 3)

type model struct {
	width, height int
	confirming    bool
	status        string
}

func (m model) Init() tea.Cmd { return nil }

// layout builds the layer stack. Both View and Update use it, so the
// hit-testing always matches what's drawn.
func (m model) layout() *lipgloss.Compositor {
	// Make the background fill the whole window so clicks on empty space
	// still land on a layer.
	bg := lipgloss.NewStyle().
		Width(m.width).
		Height(m.height).
		Render("Your main screen…\n\nPress d to open the dialog, q to quit.\n\n" + m.status)

	layers := []*lipgloss.Layer{
		lipgloss.NewLayer(bg).ID("background"),
	}

	if m.confirming {
		box := dialogStyle.Render(
			lipgloss.JoinVertical(lipgloss.Center,
				"Delete 3 files? This can't be undone.",
				"",
				"[y] Yes    [n] No",
			),
		)
		w, h := lipgloss.Size(box)
		x := max(0, (m.width-w)/2)
		y := max(0, (m.height-h)/2)

		layers = append(layers,
			lipgloss.NewLayer(box).ID("dialog").X(x).Y(y).Z(1),
		)
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
			m.confirming = true
		case "y":
			if m.confirming {
				m.confirming, m.status = false, "Confirmed."
			}
		case "n", "esc":
			if m.confirming {
				m.confirming, m.status = false, "Cancelled."
			}
		}

	case tea.MouseClickMsg:
		if !m.confirming {
			break
		}
		mouse := msg.Mouse()
		hit := m.layout().Hit(mouse.X, mouse.Y)

		switch hit.ID() {
		case "dialog":
			m.status = fmt.Sprintf("Clicked inside dialog at %d,%d", mouse.X, mouse.Y)
		default: // "background", or an empty hit
			m.confirming = false
			m.status = "Clicked outside — dialog dismissed."
		}
	}
	return m, nil
}

func (m model) View() tea.View {
	v := tea.NewView(m.layout().Render())
	v.AltScreen = true
	v.MouseMode = tea.MouseModeCellMotion // needed to receive mouse events
	return v
}

func main() {
	if _, err := tea.NewProgram(model{}).Run(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
```

**How it works:**

- **Centering:** Use `lipgloss.Size` to measure the rendered dialog, then position it at `X((width-w)/2)` and `Y((height-h)/2)`. Don't use `lipgloss.Place` for this: it pads the dialog with blank space, which would hide your background instead of drawing on top of it.
- **Z-order:** `Z(1)` puts the dialog above the background. `Hit` returns the topmost layer at that cell, so clicks on the dialog return `"dialog"`.
- **Background must fill the window:** The background gets `Width`/`Height` set to the window size. Without that, clicks on empty areas might hit no layer at all. The `default` case handles an empty hit anyway.
- **Mouse must be turned on:** In v2 you enable mouse events with `v.MouseMode` on the returned `tea.View`, not with a program option. Use `msg.Mouse()` to get `X`, `Y` and `Button`.

**Optional additions:**

- **Clickable buttons:** Give Yes/No their own layers with IDs (e.g. `"yes"`, `"no"`) and a higher Z, placed at their positions inside the box. Then check `hit.ID()` for those IDs too.
- **Dimmed background:** When the dialog is open, render `bg` with a faint style (`lipgloss.NewStyle().Faint(true)`) so the dialog stands out.

**Version note:** This is the API in the stable Lipgloss v2 release (`NewCompositor`, which returns a hit result with `.ID()`). Some earlier v2 betas used `lipgloss.NewCanvas(layers...)` instead, and `canvas.Hit(x, y)` returned the ID string directly. If `NewCompositor` doesn't exist in your version, that's the change to make.
