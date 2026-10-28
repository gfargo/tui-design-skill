**Size both children in the parent’s `Update`, and don’t render them until the initial size arrives.** Bubble Tea sends `tea.WindowSizeMsg` at startup and on resize, but Bubbles components don’t apply it themselves. A zero-sized list can render a broken fragment; a zero-sized viewport renders nothing.

For example, with a list above a viewport and one footer row:

```go
// Fields on your model:
// width, height int
// sized bool
// list list.Model
// viewport viewport.Model

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height
        m.sized = true

        bodyH := max(0, msg.Height-1) // reserve footer
        listH := bodyH / 2

        m.list.SetSize(msg.Width, listH)
        m.viewport.SetWidth(msg.Width)
        m.viewport.SetHeight(bodyH - listH)
        return m, nil
    }

    // Keep your existing child message routing here.
    // Preserve commands returned by child Update methods.
    return m, nil
}

func (m model) View() tea.View {
    content := "Initializing…"
    if m.sized {
        if m.width < 20 || m.height < 10 { // choose your real minimum
            content = "Terminal too small"
        } else {
            content = lipgloss.JoinVertical(
                lipgloss.Left,
                m.list.View(),
                m.viewport.View(),
                "tab: switch pane",
            )
        }
    }

    v := tea.NewView(content)
    v.AltScreen = true // for a full-screen app
    return v
}
```

Use your actual pane allocation: subtract headers, footers, gaps, borders, and padding before giving children their **content dimensions**. Lipgloss v2 style `Width`/`Height` already include borders and padding; margins remain outside.

For v2, construct the viewport with options, such as `viewport.New()`, then use `SetWidth` and `SetHeight`; use `list.SetSize` for the list. Initialize both components before the program starts, and keep viewport content in the model—don’t recreate the viewport on each resize.

Verify startup without touching the terminal, then send synthetic sizes for 80×24, 60×24, and your minimum. For side-by-side panes, switch to one pane at narrow widths.