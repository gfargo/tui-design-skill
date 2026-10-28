Size both components when the parent receives `tea.WindowSizeMsg`. Bubble Tea sends this at startup and again on resize; forward the resulting **available pane sizes** explicitly to each child.

```go
case tea.WindowSizeMsg:
    // Subtract borders, padding, headers, footers, and pane gaps.
    innerW := max(0, msg.Width-frameWidth)
    innerH := max(0, msg.Height-frameHeight)

    listW := min(30, innerW)
    viewportW := max(0, innerW-listW-gap)

    m.list.SetSize(listW, innerH)
    m.viewport.SetWidth(viewportW)
    m.viewport.SetHeight(innerH)
    m.ready = true

    return m, nil
```

Until that first size event, render a placeholder:

```go
func (m model) View() tea.View {
    if !m.ready {
        return tea.NewView("Loading…")
    }
    return tea.NewView(m.renderLayout())
}
```

A few details matter:

- Child components don’t automatically inherit their parent’s dimensions. Merely forwarding `WindowSizeMsg` to their `Update` methods isn’t a substitute for setting their sizes.
- In Bubbles v2, use the viewport’s `SetWidth` and `SetHeight` methods.
- Set viewport content when the content becomes available; you don’t need to wait for a resize.
- Keep the child models alive across resizes—update their sizes instead of reconstructing them.

If it works only after a manual resize, check whether startup initialization replaces an already-sized component with a fresh zero-sized one. Route both initial setup and subsequent resizes through the same layout function.