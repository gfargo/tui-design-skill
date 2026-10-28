**Size both components explicitly in the parent’s `Update` when you receive `tea.WindowSizeMsg`.** Bubble Tea sends this message at startup and on resize, but embedded Bubbles don’t automatically receive a usable layout.

The symptoms suggest the list and viewport are initially rendering with zero or placeholder dimensions.

```go
// Bubble Tea v2 / Bubbles v2.
// This example stacks the list above the viewport.
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        // Subtract outer borders, padding, and other app chrome here.
        width := max(0, msg.Width)
        height := max(0, msg.Height)

        listHeight := height / 2
        viewportHeight := height - listHeight

        m.list.SetSize(width, listHeight)
        m.viewport.SetWidth(width)
        m.viewport.SetHeight(viewportHeight)
        m.ready = width > 0 && height > 0

        return m, nil
    }

    // Route other messages to your components as appropriate.
    // Keep their returned models and commands.
    return m, nil
}

func (m model) View() tea.View {
    if !m.ready {
        return tea.NewView("Initializing…")
    }

    return tea.NewView(
        lipgloss.JoinVertical(
            lipgloss.Left,
            m.list.View(),
            m.viewport.View(),
        ),
    )
}
```

A few details matter:

- **Allocate each child its own rectangle.** Giving both the full terminal size makes the combined layout overflow.
- Subtract border/padding sizes and header/footer heights before allocating space. Use Lip Gloss frame measurements where applicable.
- Set viewport content with `SetContent` independently of sizing. If you manually wrap content to its width, rewrap from the original content after each size change.
- Avoid recreating the components on every resize; use their sizing methods to preserve selection and scroll state.

You normally don’t need to query terminal dimensions yourself. Handle the initial size message and every subsequent resize through the same layout path.