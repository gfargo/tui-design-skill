There's no Go code in this directory, so this answer is based on how Bubble Tea v2 and Bubbles v2 behave, not on your code. If you paste your `Model`, `Update`, and `View`, I can find the exact line.

## What's going on

`list.Model` and `viewport.Model` start at **0×0**. They only get a real size when you give them one. Bubble Tea sends a `tea.WindowSizeMsg` right after the program starts, not only when the terminal is resized. So if resizing fixes it, your code most likely does one of these on that first message:

1. **Forwards the message without sizing the child.** `list.Update(tea.WindowSizeMsg)` does **not** resize the list. You have to call `SetSize` yourself. The viewport doesn't resize itself from the message either.
2. **Loses the size update.** If `Update` has a value receiver and you change a copy (for example, `m.list` inside a helper) without returning it, the change is lost. Resizing seems to fix it only because later messages happen to go through a path that does save it.
3. **Creates the component after the size message arrived.** For example, the viewport is built when the user switches screens or when data loads, using `viewport.New()` with no size. The startup `WindowSizeMsg` has already come and gone, and none will arrive until the next resize.
4. **Sets content before the viewport has a width and height.** The content then isn't re-laid out when a size arrives.
5. **Doesn't subtract borders, padding, or header/footer height.** The list renders taller or wider than its space, the terminal wraps it, and you get a garbled fragment.

## The fix

Save the terminal size on your top-level model. Put all sizing in one `layout()` function and call it from two places: when the size changes, and whenever you create or replace a component.

```go
type model struct {
	width, height int
	ready         bool

	list     list.Model
	viewport viewport.Model
	content  string
}

var (
	listStyle = lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).Padding(0, 1)
	vpStyle   = lipgloss.NewStyle().Border(lipgloss.RoundedBorder())
)

func newModel(items []list.Item) model {
	l := list.New(items, list.NewDefaultDelegate(), 0, 0) // real size comes later
	vp := viewport.New()                                   // v2: options/setters, no exported Width/Height fields
	return model{list: l, viewport: vp}
}

func (m *model) layout() {
	header := lipgloss.Height(m.headerView())
	footer := lipgloss.Height(m.footerView())
	avail := m.height - header - footer

	// Example split: list on the left third, viewport on the right.
	listW := m.width / 3
	vpW := m.width - listW

	fw, fh := listStyle.GetFrameSize()
	m.list.SetSize(listW-fw, avail-fh)

	fw, fh = vpStyle.GetFrameSize()
	m.viewport.SetWidth(vpW - fw)
	m.viewport.SetHeight(avail - fh)

	// Re-wrap content to the new width; the viewport doesn't reflow it for you.
	m.viewport.SetContent(lipgloss.NewStyle().Width(m.viewport.Width()).Render(m.content))
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
		m.ready = true
		m.layout()
		return m, nil // children don't need this message once they're sized

	case contentLoadedMsg:
		m.content = string(msg)
		if m.ready {
			m.layout() // content arrived after the size: lay out again
		}
	}

	var cmd tea.Cmd
	m.list, cmd = m.list.Update(msg)
	cmds = append(cmds, cmd)
	m.viewport, cmd = m.viewport.Update(msg)
	cmds = append(cmds, cmd)

	return m, tea.Batch(cmds...)
}

func (m model) View() tea.View {
	if !m.ready {
		return tea.NewView("") // or a spinner; never render 0×0 components
	}
	body := lipgloss.JoinHorizontal(lipgloss.Top,
		listStyle.Render(m.list.View()),
		vpStyle.Render(m.viewport.View()),
	)
	return tea.NewView(lipgloss.JoinVertical(lipgloss.Left, m.headerView(), body, m.footerView()))
}
```

## Rules of thumb

- **Size flows down from the parent.** Only the top-level model handles `WindowSizeMsg`. Children get explicit sizes through `SetSize`, `SetWidth`, and `SetHeight`.
- **Measure, don't hard-code.** Use `lipgloss.Height(...)` for headers and footers, and `style.GetFrameSize()` (or `GetHorizontalFrameSize` / `GetVerticalFrameSize`) for borders and padding. If you're off by one, the terminal wraps the line and the layout breaks.
- **Call `layout()` whenever something changes the layout:** a resize, a component being created or replaced, a help bar being toggled, a status line appearing, or new content arriving.
- **Lay out viewport content after sizing, and again on width changes.** Store the raw content and re-wrap it in `layout()`.
- **Render nothing until the first size arrives.** The `ready` flag stops the first frame from showing broken 0×0 output.
- **Clamp negative sizes** (`max(0, ...)`) for very small terminals.

On the v2 API: the viewport now uses `viewport.New(...options)` with `SetWidth`/`SetHeight`/`Width()` instead of the exported `Width`/`Height` fields from v1, and `View()` returns `tea.View`. If you're on an earlier v2 beta where `View()` returns a `string`, change the return type; the sizing approach is the same.
