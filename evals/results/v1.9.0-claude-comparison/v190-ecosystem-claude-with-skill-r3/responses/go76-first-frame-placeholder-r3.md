**Short answer:** Bubble Tea doesn't size your child components. The program starts with no size, and the bubbles never read `tea.WindowSizeMsg` on their own. Until you call `SetSize`/`SetWidth`/`SetHeight` on them, the list is 0×0 and draws a broken fragment, and the viewport has height 0 and draws nothing. Resizing "fixes" it only because that's the first time your code passes real dimensions down.

The fix has four parts:
1. Save the size in your model.
2. Work out every child's size in one `layout()` function.
3. Call it whenever a `WindowSizeMsg` arrives.
4. Have `View` show a placeholder until the first size arrives.

### The pattern

```go
type model struct {
    list          list.Model
    viewport      viewport.Model
    width, height int
}

const minW, minH = 40, 10

// One place that turns the terminal size into child sizes.
// Pointer receiver: SetSize on a copy is silently lost.
func (m *model) layout() {
    // Measure your header and footer instead of hard-coding "-2".
    bodyH := m.height - lipgloss.Height(m.headerView()) - lipgloss.Height(m.footerView())

    if m.width >= 100 { // wide: list | viewport side by side
        listW := m.width / 3
        m.list.SetSize(listW, bodyH)
        m.viewport.SetWidth(m.width - listW)
        m.viewport.SetHeight(bodyH)
    } else { // narrow (e.g. a 60-col tmux split): stack them, or show one pane at a time
        listH := bodyH / 2
        m.list.SetSize(m.width, listH)
        m.viewport.SetWidth(m.width)
        m.viewport.SetHeight(bodyH - listH)
    }
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height
        m.layout()
        // If you pre-wrapped viewport content to a width, re-render it now:
        // m.viewport.SetContent(m.renderDetail())
        return m, nil
    }
    // ...forward keys to the focused child, keep the returned Cmds...
    return m, nil
}

func (m model) View() tea.View {
    if m.width == 0 { // no WindowSizeMsg yet: every child is still zero-sized
        return tea.NewView("loading…")
    }
    if m.width < minW || m.height < minH {
        return tea.NewView(fmt.Sprintf("Terminal too small (%d×%d, need %d×%d)",
            m.width, m.height, minW, minH))
    }
    return tea.NewView(lipgloss.JoinVertical(lipgloss.Left,
        m.headerView(), m.body(), m.footerView()))
}
```

### Common mistakes

- **Value receivers.** If `layout()` or a helper takes `model` by value, or `Update` doesn't return the changed `m`, the sizes are lost. That can look exactly like "only works after resize."
- **Hard-coded chrome.** Writing `msg.Height - 2` breaks as soon as the header wraps or you add a status line. Measure the header and footer with `lipgloss.Height`.
- **Borders in lipgloss v2.** `Width`/`Height` now include the border and padding. If panes have borders, give each child `paneW - style.GetHorizontalFrameSize()` (and the vertical equivalent). Old v1 math like `Width(w-2)` now comes out 2 cells too narrow.
- **v2 API.** The viewport uses `SetWidth`/`SetHeight`, or `viewport.New(viewport.WithWidth(..), viewport.WithHeight(..))`. The list still uses `SetSize`.
- **Width-dependent content.** If you wrap or truncate the viewport's text to its width yourself, rebuild it on every resize. Otherwise it keeps the startup width.
- **Don't guess a startup size.** Don't hard-code 80×24 or query the terminal yourself. Bubble Tea sends a `WindowSizeMsg` right after startup, so the placeholder is visible for only a moment.

### Small terminals

At 80×24 the side-by-side layout gives the list about 26 columns, which is fine. In a 60-column split it's too cramped, so the narrow branch stacks the panes. You could also show only the list and open the viewport as a drill-down on Enter. Below `minW`×`minH`, the "too small" message is better than a mangled layout.

### Testing it

- **Unit test:** call `Update` with `tea.WindowSizeMsg{Width: 60, Height: 24}`, then check `m.viewport.Height()` and the list's size. Send a second size to confirm the layout reflows and doesn't keep the startup width.
- **Golden test:** use `teatest/v2` with `teatest.WithInitialTermSize(80, 24)` and `tea.WithColorProfile(colorprofile.ASCII)`. Keep one golden file each for 80×24, 60 columns, and your minimum size.
