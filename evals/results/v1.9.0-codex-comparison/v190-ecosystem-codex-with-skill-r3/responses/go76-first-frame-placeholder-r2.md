**Size both children explicitly in the parent’s `Update`, and render a placeholder until the first size arrives.** Your symptoms match zero-sized components: a list renders a broken fragment, while a viewport renders nothing.

Bubble Tea delivers `tea.WindowSizeMsg` at startup and on resize. Bubbles do **not** apply that message themselves; forwarding it to their `Update` methods is insufficient.

For example, with the list above the viewport:

```go
// Fields on your parent model:
// width, height int
// list         list.Model
// viewport     viewport.Model

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height

        // Example: reserve one row for the parent's footer.
        bodyH := max(0, msg.Height-1)
        listH := bodyH / 2
        viewportH := bodyH - listH

        m.list.SetSize(msg.Width, listH)
        m.viewport.SetWidth(msg.Width)
        m.viewport.SetHeight(viewportH)
        return m, nil
    }

    // Keep your normal child updates and returned commands here.
    // Route keyboard input to the focused child.
    return m, nil
}

func (m model) View() tea.View {
    content := "Initializing…"
    if m.width > 0 && m.height > 0 {
        content = lipgloss.JoinVertical(
            lipgloss.Left,
            m.list.View(),
            m.viewport.View(),
            "tab switch pane · ctrl+c quit",
        )
    }

    v := tea.NewView(content)
    v.AltScreen = true // For a full-screen app.
    return v
}
```

Use imports from `charm.land/bubbletea/v2`, `charm.land/bubbles/v2/...`, and `charm.land/lipgloss/v2`.

A few sizing rules matter:

- Allocate each child its **own content rectangle**, subtracting parent headers, footers, gaps, borders, and padding. The list manages its own internal title/help.
- In Lipgloss v2, styled `Width`/`Height` **include borders and padding**. Subtract those when calculating the child’s inner space.
- Load viewport content with `SetContent(...)`; resizing only supplies its visible dimensions.
- Handle tiny terminals explicitly instead of rendering unusably short children. At 80×24 and 60 columns, check that both panes remain useful; otherwise show only the focused pane.

Verify the fix by rendering before any size message, then sending synthetic `WindowSizeMsg`s for startup, shrink, and grow. Both children should receive valid dimensions without requiring a manual resize.