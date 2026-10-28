The usual approach is to draw the dialog as a layer with Lipgloss v2's `Compositor`. In `View`, put your screen in a full-window base layer and the dialog in a higher layer, then build a compositor from them. In `v.OnMouse`, call `comp.Hit(x, y)` to find which layer is under the click, and send the result to `Update` as a message.

Things that will catch you out (from the skill's Go reference):

- **IDs:** `Hit` only returns layers that have an `ID`, so give an ID to every layer a click can land on, including the base.
- **Z values:** `Z` is compared as written, not added to a parent layer's `Z`. Equal values have no defined order, so give each layer its own value.
- **Window size:** make the base layer exactly the window size and keep the dialog inside it. A layer that sticks out makes the frame bigger.
- **One click handler:** `OnMouse` runs against the last frame drawn, so its closure can use the `comp` built in that `View`. `Update` also receives the raw `tea.MouseClickMsg`. Handle clicks in only one of the two places.

## Example

I haven't compiled or run this code.

```go
package main

import (
	"log"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

type hitMsg string // layer ID under a click: "base", "dialog", "cancel", "confirm"

type confirm struct {
	title, body string
	focusYes    bool    // false = Cancel focused, so Enter is safe
	onConfirm   tea.Cmd // the real action, run only on confirm
}

type model struct {
	width, height int
	body          string
	confirming    bool
	dlg           confirm
}

var (
	dialogStyle = lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).Padding(1, 2)
	titleStyle  = lipgloss.NewStyle().Bold(true)
	btnStyle    = lipgloss.NewStyle()
	btnFocus    = lipgloss.NewStyle().Reverse(true)
)

// Brackets show focus even when the terminal ignores reverse or NO_COLOR is set.
func button(label string, focused bool) string {
	if focused {
		return btnFocus.Render("[" + label + "]")
	}
	return btnStyle.Render(" " + label + " ")
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height

	case hitMsg:
		if !m.confirming {
			return m, nil // route base-screen clicks here ("base" or your own IDs)
		}
		switch msg {
		case "confirm":
			return m.resolve(true)
		case "cancel", "base": // clicking the background cancels, like Esc
			return m.resolve(false)
		}
		// "dialog": a click inside the box but not on a button does nothing

	case tea.KeyPressMsg:
		if msg.String() == "ctrl+c" {
			return m, tea.Quit
		}
		if m.confirming { // the dialog keeps focus: no keys reach the base screen
			switch msg.String() {
			case "y":
				return m.resolve(true)
			case "n", "esc":
				return m.resolve(false)
			case "tab", "shift+tab", "left", "right", "h", "l":
				m.dlg.focusYes = !m.dlg.focusYes
			case "enter":
				return m.resolve(m.dlg.focusYes)
			}
			return m, nil
		}
		switch msg.String() {
		case "q":
			return m, tea.Quit
		case "d":
			m.confirming = true
			m.dlg = confirm{title: "Delete 3 files?", body: "This cannot be undone.", onConfirm: nil /* deleteCmd */}
		}
	}
	return m, nil
}

func (m model) resolve(yes bool) (tea.Model, tea.Cmd) {
	m.confirming = false
	if yes {
		return m, m.dlg.onConfirm
	}
	return m, nil
}

func (m model) View() tea.View {
	base := lipgloss.NewStyle().Width(m.width).Height(m.height)
	if m.confirming {
		base = base.Faint(true) // a nice extra; the border, title and buttons still mark the dialog
	}
	layers := []*lipgloss.Layer{lipgloss.NewLayer(base.Render(m.body)).ID("base")}

	if m.confirming {
		// 70% of the width, between 30 and 60 columns, never wider than the window
		w := min(max(m.width*7/10, 30), 60, m.width)
		no := button("Cancel", !m.dlg.focusYes)
		yes := button("Delete", m.dlg.focusYes)
		box := dialogStyle.Width(w).Render(lipgloss.JoinVertical(lipgloss.Left,
			titleStyle.Render(m.dlg.title), "", m.dlg.body, "",
			lipgloss.JoinHorizontal(lipgloss.Top, no, "  ", yes),
		))
		bw, bh := lipgloss.Width(box), lipgloss.Height(box)
		x := max(0, (m.width-bw)/2)
		y := max(0, (m.height-bh)/2-1) // a little above center
		layers = append(layers, lipgloss.NewLayer(box).ID("dialog").X(x).Y(y).Z(1))

		// Redraw each button as its own layer on top so Hit can tell them apart.
		bx := x + dialogStyle.GetBorderLeftSize() + dialogStyle.GetPaddingLeft()
		by := y + bh - 1 - dialogStyle.GetBorderBottomSize() - dialogStyle.GetPaddingBottom()
		layers = append(layers,
			lipgloss.NewLayer(no).ID("cancel").X(bx).Y(by).Z(2),
			lipgloss.NewLayer(yes).ID("confirm").X(bx+lipgloss.Width(no)+2).Y(by).Z(2),
		)
	}

	comp := lipgloss.NewCompositor(layers...)
	v := tea.NewView(comp.Render())
	v.AltScreen = true
	v.MouseMode = tea.MouseModeCellMotion
	v.OnMouse = func(msg tea.MouseMsg) tea.Cmd {
		if c, ok := msg.(tea.MouseClickMsg); ok && c.Button == tea.MouseLeft {
			id := comp.Hit(c.X, c.Y).ID() // "" if no layer with an ID is there
			return func() tea.Msg { return hitMsg(id) }
		}
		return nil
	}
	return v
}

func main() {
	if _, err := tea.NewProgram(model{body: "your existing screen…"}).Run(); err != nil {
		log.Fatal(err)
	}
}
```

## Design choices

- **Keyboard first, mouse optional.** `y`/`n`, `Esc`, Tab or the arrow keys, and `Enter` do everything. The mouse is just a shortcut. Cancel has focus when the dialog opens, so pressing `Enter` by reflex doesn't delete anything.
- **Clicking the background cancels; it never confirms.** That makes it the same as `Esc` and keeps the click away from your main screen. If accidental dismissals are a problem, make `"base"` do nothing, like `"dialog"`.
- **The dialog has a solid background.** Lipgloss fills the padding with spaces, so the text underneath doesn't show through. Dimming the background with `Faint` is a nice extra, but some terminals ignore faint text. The border, title and bracketed button still make it clear you're in a dialog.
- **Small terminals:** at 60 columns the dialog is 42 wide, and it never shrinks below 30 columns. Clamping `x`/`y` to 0 and `w` to `m.width` keeps it inside the window, so the frame never grows. On a terminal narrower than 30 columns, show your "terminal too small" message instead.

## Testing

Because clicks reach `Update` as `hitMsg`, you can unit-test without a terminal. Send `hitMsg("base")`, `hitMsg("confirm")` and key presses to `Update`, and check `confirming` and the returned command. Then golden-test `View()` at 80×24 and 60 columns to check where the dialog and button layers land. A test that renders `View()` and calls `comp.Hit` on the button's cells catches mistakes in the button offset math.
