Use the **real terminal cursor** and pass its position to the parent `tea.View`. The default virtual cursor only paints a cell; the IME follows the terminal cursor, which can remain at the bottom-left.

```go
// When initializing the input:
m.input = textinput.New()
m.input.SetVirtualCursor(false)
m.input.Focus()

func (m model) View() tea.View {
    v := tea.NewView("Search\n" + m.input.View())

    if c := m.input.Cursor(); c != nil {
        c.Y++ // Account for the heading above the input.
        v.Cursor = c
    }

    return v
}
```

Use v2 imports: `charm.land/bubbletea/v2` and `charm.land/bubbles/v2/textinput`.

Add the input’s actual layout offset to `c.X` and `c.Y`, including borders, padding, labels, and pane placement. Recalculate it when the layout changes. `Cursor()` returns `nil` while blurred; blur the input when an overlay covers it.

**Japanese-text caveat:** the skill documents that Bubbles v2.2.1’s `textinput.Cursor()` counts runes rather than terminal cells, so wide CJK characters can still shift the position left. If that remains after this fix, use a release with corrected width handling or patch the cursor calculation to measure the visible prefix in terminal cells, accounting for horizontal scrolling.

Verify with an actual Japanese IME, including committed CJK text, caret movement, and terminal resizing.