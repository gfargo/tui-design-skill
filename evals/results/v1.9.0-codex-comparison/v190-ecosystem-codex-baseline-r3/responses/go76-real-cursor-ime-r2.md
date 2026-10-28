Use a **real terminal cursor** and pass its position through your top-level `tea.View`. The IME anchors its candidate window to that cursor; a virtual cursor is only painted text.

With current Bubbles v2:

```go
import (
    "charm.land/bubbles/v2/textinput"
    tea "charm.land/bubbletea/v2"
)

// During model construction:
input := textinput.New()
input.SetVirtualCursor(false)
// Ensure the input is focused; return its Focus() command as usual.
```

Then expose its cursor on every render:

```go
func (m model) View() tea.View {
    // The input starts at column 2, row 1.
    v := tea.NewView("Name:\n  " + m.input.View())

    if c := m.input.Cursor(); c != nil {
        c.Position.X += 2
        c.Position.Y += 1
        v.Cursor = c
    }

    return v
}
```

The offsets must match the input’s actual location, including surrounding borders, padding, and content above it. Use terminal **cell widths**, not byte lengths, when calculating horizontal offsets. `input.Cursor()` supplies the position within the widget. citeturn603580search2

On older v2 prereleases, use `input.VirtualCursor = false` instead of the setter. Returning only the rendered input string without assigning `v.Cursor` leaves the IME anchor misplaced. citeturn603580search3turn380975view1