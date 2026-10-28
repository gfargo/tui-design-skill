Build the frame from two Lipgloss v2 layers: the full-window screen as the bottom layer and the dialog as a centered layer above it. Give each layer an ID. The `Compositor` that draws the frame can also tell you which layer is at a given cell, so `comp.Hit(x, y).ID()` returns `"dialog"` or `"base"` for a click.

```go
package main

import (
	"log"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

type hitMsg string // ID of the top-most layer under a click; "" if none

type model struct {
	width, height int
	body          string
	confirming    bool
	status        string
}

var dialogStyle = lipgloss.NewStyle().
	BorderStyle(lipgloss.RoundedBorder()).
	Padding(1, 2)

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height

	case tea.KeyPressMsg:
		if msg.String() == "ctrl+c" {
			return m, tea.Quit
		}
		if m.confirming { // the modal traps focus
			switch msg.String() {
			case "y":
				m.confirming, m.status = false, "deleted"
				// return m, deleteCmd  ← do the real work in a Cmd, never in Update
			case "n", "esc", "enter": // Enter means No
				m.confirming, m.status = false, "cancelled"
			}
			return m, nil
		}
		switch msg.String() {
		case "d":
			m.confirming = true
		case "q":
			return m, tea.Quit
		}

	case hitMsg: // every click is handled here; ignore raw tea.MouseClickMsg
		if !m.confirming {
			return m, nil
		}
		switch msg {
		case "dialog":
			// Inside the dialog: do nothing, or route to buttons (see below)
		default: // "base" or "": a click outside cancels, the safe choice
			m.confirming, m.status = false, "cancelled"
		}
	}
	return m, nil
}

func (m model) View() tea.View {
	if m.width == 0 { // no WindowSizeMsg yet
		return tea.NewView("")
	}

	// The base layer fills the window exactly. A layer that hangs off the edge makes the frame larger.
	base := lipgloss.NewStyle().
		Width(m.width).Height(m.height).
		Faint(m.confirming). // dims the background; the border carries the meaning when faint is ignored
		Render(m.body + "\n\n" + m.status)

	layers := []*lipgloss.Layer{lipgloss.NewLayer(base).ID("base")}

	if m.confirming {
		// 70% of the width, kept between 30 and 80 columns (v2 Width includes border and padding)
		w := min(max(m.width*7/10, 30), 80, m.width)
		box := dialogStyle.Width(w).Render(
			"Delete 3 files?\n\n[y] Yes   [N] No   esc cancel")
		x := (m.width - lipgloss.Width(box)) / 2
		y := max((m.height-lipgloss.Height(box))*2/5, 0) // a little above center
		layers = append(layers, lipgloss.NewLayer(box).ID("dialog").X(x).Y(y).Z(1))
	}

	comp := lipgloss.NewCompositor(layers...)
	v := tea.NewView(comp.Render())
	v.AltScreen = true
	v.MouseMode = tea.MouseModeCellMotion
	v.OnMouse = func(msg tea.MouseMsg) tea.Cmd {
		if c, ok := msg.(tea.MouseClickMsg); ok {
			id := comp.Hit(c.X, c.Y).ID()
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

## Why it works

- **`Hit` only finds layers that have an ID.** It returns the top-most layer *with an ID* at that cell. Leave the base layer without one and background clicks return `""`. The code above treats `""` and `"base"` the same way.
- **`OnMouse` uses the frame that was last drawn.** The closure holds on to the `comp` built in that `View()`, so the hit test matches what the user saw.
- **Clicks arrive twice.** Bubble Tea also sends the raw `tea.MouseClickMsg` to `Update`. Handle clicks in one place only, which here is `hitMsg`, or each click will run twice.
- **`Z` values are compared exactly as written.** They are not added to a parent's `Z`, whatever the doc comment suggests. When two layers have the same `Z`, which one is on top is undefined, so give every layer a different value.
- **Sizes in v2 include the border and padding.** `Width(w)` is the full width of the box. Code ported from v1 that does `Width(w-2)` will come out 2 columns too narrow.

## Clickable Yes/No buttons

Render each button as its own layer, for example `ID("yes")` and `ID("no")`. Give them `Z(2)` and place them at absolute coordinates you work out from the dialog's `x`/`y` plus the border and padding. Then add `case "yes"` and `case "no"` to the `hitMsg` switch. Keep the `y`/`n` keys too, because the mouse should never be the only way to do something.

## Design points for the dialog

- **No is the default.** Enter, Esc, and a click outside all cancel. A stray click or keypress should never delete anything.
- **Show it's a dialog without relying on dim text.** Some terminals ignore faint, and `NO_COLOR` turns off color. The border and the key hints inside the box still show that the dialog is open. Also change your footer hints while it's open.
- **Faint on text that already has styling:** if `m.body` already contains ANSI styles, their reset codes can cancel the faint. Apply the dimmed style where you render the body instead of wrapping the finished string.
- **Provide a way to turn the mouse off.** Mouse capture prevents normal text selection: users must hold Shift, or Option in iTerm2, to select. Offer a `--no-mouse` flag that leaves `MouseMode` unset.

## Sizes

```
80×24                                     60 cols (tmux split)
┌ dimmed screen ───────────────────────┐   ┌ dimmed ─────────────────────┐
│      ╭──────────────────────────╮    │   │ ╭─────────────────────────╮ │
│      │  Delete 3 files?         │    │   │ │  Delete 3 files?        │ │
│      │  [y] Yes [N] No esc      │    │   │ │  [y] Yes [N] No esc     │ │
│      ╰──────────────────────────╯    │   │ ╰─────────────────────────╯ │
└──────────────────────────────────────┘   └─────────────────────────────┘
```

At 80 columns the box is 56 wide (70%). At 60 columns it's 42. Below 30 columns the box would hang off the screen and make the frame larger, so show a "terminal too small" message instead.

I haven't compiled this code. To test it, send `hitMsg("base")`, `hitMsg("dialog")`, and key presses such as `tea.KeyPressMsg{Code: 'y', Text: "y"}` to `Update` and check `confirming` and `status`. Also save golden snapshots of the rendered frame at 80×24 and at 60 columns.
