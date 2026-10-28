**Size both children explicitly in the parent’s `Update`, and render a placeholder until the first `tea.WindowSizeMsg`.** Bubble Tea delivers terminal dimensions at startup and on resize, but embedded Bubbles don’t apply that message themselves.

A zero-sized list can render a broken fragment; a zero-sized viewport renders nothing. Simply forwarding the message through their `Update` methods won’t size them.

For example, with the list stacked above the viewport:

```go
// Imports use charm.land/bubbletea/v2,
// charm.land/bubbles/v2/{list,viewport}, and charm.land/lipgloss/v2.

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height

        // Reserve one row for the parent's footer.
        bodyHeight := max(0, msg.Height-1)
        listHeight := bodyHeight / 2
        viewportHeight := bodyHeight - listHeight

        m.list.SetSize(msg.Width, listHeight)
        m.viewport.SetWidth(msg.Width)
        m.viewport.SetHeight(viewportHeight)
        return m, nil
    }

    // Keep your normal child Update routing and returned commands here.
    return m, nil
}

func (m model) View() tea.View {
    content := "Initializing…"
    if m.width > 0 && m.height > 0 {
        content = lipgloss.JoinVertical(lipgloss.Left,
            m.list.View(),
            m.viewport.View(),
            "tab: switch focus",
        )
    }

    v := tea.NewView(content)
    v.AltScreen = true // For a full-screen app.
    return v
}
```

Apply the same layout calculation on **every** size message. Allocate each child its available content area after parent headers, footers, padding, borders, and gaps. In Lipgloss v2, styled `Width` and `Height` include border and padding; account for those when computing the inner child dimensions.

Initialize viewport content with `SetContent` independently of sizing. If you wrap or render Markdown to a fixed width yourself, regenerate that content when the viewport width changes.

At 80×24 and 60 columns, verify that both regions remain usable; switch side-by-side panes to stacked or focused-pane views when needed. For sizes below your usable minimum, show “Terminal too small” instead of rendering children with unusable dimensions.

A useful regression check is: render before any size message, send `WindowSizeMsg{Width: 80, Height: 24}`, then send a 60-column resize and assert both children’s dimensions. No forced redraw or synthetic resize should be necessary.