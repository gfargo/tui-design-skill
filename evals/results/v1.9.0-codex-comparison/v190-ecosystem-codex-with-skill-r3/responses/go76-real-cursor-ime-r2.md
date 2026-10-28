Use the **real terminal cursor** for the input. The default virtual cursor is a styled cell; the IME follows the terminal’s actual cursor, which can remain at the bottom-left.

```go
// When creating the input:
m.input = textinput.New()
m.input.SetVirtualCursor(false)
m.input.Focus()

func (m model) View() tea.View {
    v := tea.NewView("Search\n" + m.input.View())

    if c := m.input.Cursor(); c != nil {
        c.Y++ // Account for the "Search" line.
        v.Cursor = c
    }

    return v
}
```

Add any surrounding layout offsets to `c.X` and `c.Y`: borders, padding, headers, and pane placement. Coordinates are zero-based terminal cells, relative to the returned frame. Recompute them each frame as the layout changes. `Cursor()` returns `nil` when the input is blurred; blur it when a modal covers it.

**Japanese-text caveat:** the skill documents that Bubbles **v2.2.1 `textinput.Cursor()` counts runes rather than display cells**, so wide CJK characters and emoji can still shift the caret left. If you see that after enabling the real cursor, check your Bubbles version for a fix or patch the cursor calculation to use display-cell widths and account for horizontal scrolling. `len()` or a rune index alone won’t work.

Verify with Japanese composition after existing CJK text, horizontal scrolling, and a terminal resize.