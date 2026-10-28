Use the **real terminal cursor** for the input and pass its position through your parent `tea.View`. IME candidate windows follow the terminal cursor; Bubbles’ default virtual cursor only paints a styled cell, leaving the IME anchored elsewhere.

```go
// When constructing the input:
m.input = textinput.New()
m.input.SetVirtualCursor(false)
m.input.Focus()
```

Then publish its cursor on every frame:

```go
func (m model) View() tea.View {
    v := tea.NewView("Search\n" + m.input.View())

    if c := m.input.Cursor(); c != nil {
        c.Y++ // input starts below the "Search" line
        v.Cursor = c
    }

    return v
}
```

Add any layout offsets to `c.X` and `c.Y`, including borders, padding, labels, and panel placement. Coordinates are zero-based terminal cells relative to the frame. Blur the input when another control or overlay takes focus; `Cursor()` returns `nil` while blurred.

**Japanese text caveat:** Bubbles v2.2.1’s `textinput.Cursor()` counts runes rather than display cells, so it can drift after wide CJK characters or emoji. If that happens, use a version with that bug fixed or patch the cursor calculation to measure the **visible text before the caret** in terminal cells, accounting for horizontal scrolling.

Verify with an actual Japanese IME: compose, select a candidate, move through committed Japanese text, and resize the terminal. A render snapshot cannot verify the OS candidate window’s position.