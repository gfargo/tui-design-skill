Lipgloss v2 has layer compositing with hit testing built in. Put the background and the dialog in separate layers, combine them with a compositor, and ask the compositor which layer is under the mouse.

The idea:

1. Render the main screen as a normal string.
2. Render the dialog as its own string and work out its centered `x, y` from the window size.
3. Wrap each one in a `lipgloss.Layer` with an ID and a Z-order, then combine them with `lipgloss.NewCompositor`.
4. On a `tea.MouseClickMsg`, call `compositor.Hit(x, y)`. It returns the topmost layer at that cell.

```go
package main

import (
	"fmt"
	"os"
	"strings"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

type model struct {
	width, height int
	showDialog    bool
	status        string
}

var (
	dialogStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("205")).
			Padding(1, 3)
	buttonStyle = lipgloss.NewStyle().
			Padding(0, 2).
			Background(lipgloss.Color("238"))
	activeButton = buttonStyle.Background(lipgloss.Color("205"))
)

func (m model) Init() tea.Cmd { return nil }

// background renders your normal screen, filling the window.
func (m model) background() string {
	body := fmt.Sprintf("Main screen\n\nStatus: %s\n\nPress d to open the dialog, q to quit.", m.status)
	return lipgloss.NewStyle().Width(m.width).Height(m.height).Render(body)
}

// layers builds the compositor for the current frame. View and Update both
// call it, so hit testing always uses the same geometry as the drawn frame.
func (m model) layers() *lipgloss.Compositor {
	layers := []*lipgloss.Layer{
		lipgloss.NewLayer(m.background()).ID("background").Z(0),
	}

	if m.showDialog {
		yes := activeButton.Render("Yes")
		no := buttonStyle.Render("No")
		buttons := lipgloss.JoinHorizontal(lipgloss.Top, yes, "  ", no)
		dialog := dialogStyle.Render(
			lipgloss.JoinVertical(lipgloss.Center, "Are you sure?", "", buttons),
		)

		// Center the dialog in the window.
		dw, dh := lipgloss.Width(dialog), lipgloss.Height(dialog)
		dx := max(0, (m.width-dw)/2)
		dy := max(0, (m.height-dh)/2)

		// Optional: give each button its own layer on top so clicks can be
		// matched to a specific button. Offsets come from the dialog layout:
		// border (1) + padding.
		innerW := dw - 2 - 6 // border + horizontal padding
		bx := dx + 1 + 3 + (innerW-lipgloss.Width(buttons))/2
		by := dy + 1 + 1 + 2 // border + top padding + 2 lines of text

		layers = append(layers,
			lipgloss.NewLayer(dialog).ID("dialog").X(dx).Y(dy).Z(1),
			lipgloss.NewLayer(yes).ID("yes").X(bx).Y(by).Z(2),
			lipgloss.NewLayer(no).ID("no").X(bx+lipgloss.Width(yes)+2).Y(by).Z(2),
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
			m.showDialog = true
		case "esc":
			m.showDialog = false
		}

	case tea.MouseClickMsg:
		mouse := msg.Mouse()
		if mouse.Button != tea.MouseLeft {
			break
		}
		hit := m.layers().Hit(mouse.X, mouse.Y)

		switch hit.ID() {
		case "yes":
			m.status, m.showDialog = "confirmed", false
		case "no":
			m.status, m.showDialog = "cancelled", false
		case "dialog":
			// Clicked inside the dialog but not on a button; ignore.
		case "background", "":
			if m.showDialog {
				// Click outside the dialog closes it (like a modal backdrop).
				m.status, m.showDialog = "dismissed by clicking outside", false
			} else {
				m.status = fmt.Sprintf("clicked background at %d,%d", mouse.X, mouse.Y)
			}
		}
	}
	return m, nil
}

func (m model) View() tea.View {
	var content string
	if m.width == 0 {
		content = "loading..."
	} else {
		content = m.layers().Render()
	}
	v := tea.NewView(strings.TrimRight(content, "\n"))
	v.AltScreen = true
	v.MouseMode = tea.MouseModeCellMotion // required to receive mouse events
	return v
}

func main() {
	if _, err := tea.NewProgram(model{status: "idle"}).Run(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
```

**Things to watch for:**

- **Mouse events are off by default.** In v2 you turn them on per frame in `View()` with `v.MouseMode = tea.MouseModeCellMotion` (or `MouseModeAllMotion` for hover). There's no longer a program option for this.
- **Z decides which layer wins.** `Hit` returns the layer with the highest Z at that cell. So the buttons (Z 2) beat the dialog (Z 1), which beats the background (Z 0).
- **Treat an empty ID as background.** If the background doesn't fill the whole window, clicks on empty cells return an empty hit. Handling `""` the same as `"background"` covers that, and `hit.Empty()` also works.
- **Hit-test against the same layout you drew.** Building the compositor in one helper (`layers()`) means `Update` and `View` always agree on positions. If you cache positions instead, recompute them on every `WindowSizeMsg`.
- **Button offsets depend on your style.** If you change the dialog's border or padding, update the `bx`/`by` math. If you only need "inside vs. outside the dialog," leave out the button layers and check for `"dialog"`.

**Version note:** this uses the v2 module paths (`charm.land/...`). If you're on an early v2 beta (`github.com/charmbracelet/...`), the same idea was spelled `lipgloss.NewCanvas(layers...)` and `canvas.Hit(x, y)`, which returned the ID string directly. If the names don't compile, check `go doc charm.land/lipgloss/v2 Compositor`.
