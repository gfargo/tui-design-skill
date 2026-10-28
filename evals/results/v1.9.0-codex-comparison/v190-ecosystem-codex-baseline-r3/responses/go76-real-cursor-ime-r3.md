The IME anchors its candidate window to the **terminal’s real cursor**. A virtual cursor drawn by `textinput` doesn’t move that cursor, so the window appears in the wrong place.

Disable the virtual cursor and pass the input’s cursor through your Bubble Tea v2 view:

```go
// When initializing the input:
m.input.SetVirtualCursor(false)
m.input.Focus()

func (m model) View() tea.View {
    v := tea.NewView(m.input.View())
    v.Cursor = m.input.Cursor()
    return v
}
```

If the input is inside a larger layout, offset its cursor to match its rendered position:

```go
func (m model) View() tea.View {
    v := tea.NewView("Name:\n" + m.input.View())

    if c := m.input.Cursor(); c != nil {
        c.Y += 1 // One line above the input.
        v.Cursor = c
    }
    return v
}
```

Include any surrounding padding, borders, or preceding content in those offsets. Use terminal **cell coordinates**, not byte counts—especially for Japanese text. The input’s `Cursor()` handles its internal text positioning; you supply the layout offset.