Use the **real terminal cursor** and pass its position through your top-level `tea.View`. The IME anchors its candidate window to the terminal cursor; a virtual cursor only paints a cursor into the text.

During initialization:

```go
ti := textinput.New()
ti.SetVirtualCursor(false)
ti.Focus()
```

Then in your model’s view:

```go
func (m model) View() tea.View {
    v := tea.NewView("Name:\n  " + m.input.View())

    v.Cursor = m.input.Cursor()
    if v.Cursor != nil {
        v.Cursor.Position.X += 2 // two spaces before the input
        v.Cursor.Position.Y += 1 // label line above the input
    }

    return v
}
```

Adjust the offsets to match your layout, including padding, borders, and any preceding content. Coordinates use terminal cells, starting at zero. `input.Cursor()` already includes the input’s own prompt offset, so don’t add that again.

Both steps matter: `SetVirtualCursor(false)` enables the real cursor, and assigning `v.Cursor` tells Bubble Tea where to put it. `Cursor()` returns `nil` when the input is unfocused or virtual cursor mode is enabled.