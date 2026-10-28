Size both components explicitly in the parent model’s `Update`, using **`tea.WindowSizeMsg` on startup and every resize**. Bubble Tea sends an initial size message automatically; embedded Bubbles don’t lay themselves out to fill the parent.

For example, with a list and viewport side by side:

```go
case tea.WindowSizeMsg:
    // Subtract your outer borders, padding, header, and footer.
    width := max(0, msg.Width-horizontalChrome)
    height := max(0, msg.Height-verticalChrome)

    listWidth := width / 3
    viewportWidth := width - listWidth

    m.list.SetSize(listWidth, height)
    m.viewport.SetWidth(viewportWidth)
    m.viewport.SetHeight(height)
    m.ready = true

    return m, nil
```

Use the v2 viewport setters, `SetWidth` and `SetHeight`. Account for any gap or individual pane borders in the allocated sizes too.

Before the first size message, render a placeholder instead of components constructed with zero dimensions:

```go
func (m model) View() tea.View {
    if !m.ready {
        return tea.NewView("Loading…")
    }
    return tea.NewView(
        lipgloss.JoinHorizontal(
            lipgloss.Top,
            m.list.View(),
            m.viewport.View(),
        ),
    )
}
```

Set viewport content with `SetContent` when it becomes available. If you manually wrap content to the viewport width, recalculate that wrapping after sizing.

If resizing fixes startup, check that your initial `WindowSizeMsg` reaches this same layout code—especially if you create or replace child models after the initial message. Cache the terminal dimensions and apply them whenever a child is created. **Keep sizing out of `View`; `View` should only render.**