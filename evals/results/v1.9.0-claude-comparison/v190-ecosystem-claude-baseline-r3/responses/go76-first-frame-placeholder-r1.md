There's no Go code in the working directory, so this answer is based on how Bubble Tea v2 and Bubbles behave in general, not on your code.

## Why this happens

- `list.New(items, delegate, 0, 0)` and a viewport created without a width or height both start at **0×0**. The list then draws with no room, which gives you the garbled fragment. A viewport with zero height shows nothing.
- Bubble Tea sends a `tea.WindowSizeMsg` when the program starts. Neither component handles that message on its own, so the parent model has to catch it and pass sizes down. If that only happens on resize, or the update gets lost, nothing fixes the layout until you resize the terminal.

## The pattern

1. **Size everything in one place.** Handle `tea.WindowSizeMsg` in the parent's `Update`. Work out each child's space by subtracting borders, padding, headers and footers. Then call each child's setter.
2. **Don't render until you have a size.** Keep a `ready` flag, or check `width == 0`, and show a placeholder until it's set.
3. **Set the viewport's content after sizing, and again on every resize.** If you wrap the text yourself, re-wrap it to the new width.
4. **Always keep the returned child model.** Bubbles components are values. `m.list.Update(msg)` without the assignment throws the change away.

```go
type model struct {
	list     list.Model
	viewport viewport.Model
	ready    bool
	width    int
	height   int
}

var (
	listStyle = lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).Padding(0, 1)
	vpStyle   = lipgloss.NewStyle().Border(lipgloss.RoundedBorder())
)

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
		m.layout()
		m.ready = true
		return m, nil // don't forward the raw size msg to children
	}

	var cmd tea.Cmd
	m.list, cmd = m.list.Update(msg) // reassign!
	cmds = append(cmds, cmd)
	m.viewport, cmd = m.viewport.Update(msg)
	cmds = append(cmds, cmd)
	return m, tea.Batch(cmds...)
}

// layout is the single source of truth for child dimensions.
func (m *model) layout() {
	footerH := lipgloss.Height(m.footerView())
	bodyH := m.height - footerH

	listW := m.width / 3
	lfw, lfh := listStyle.GetFrameSize() // border + padding
	m.list.SetSize(listW-lfw, bodyH-lfh)

	vfw, vfh := vpStyle.GetFrameSize()
	m.viewport.SetWidth(m.width - listW - vfw)
	m.viewport.SetHeight(bodyH - vfh)
	m.viewport.SetContent(m.renderContent()) // re-wrap to the new width
}

func (m model) View() tea.View {
	if !m.ready {
		return tea.NewView("Initializing…")
	}
	body := lipgloss.JoinHorizontal(lipgloss.Top,
		listStyle.Render(m.list.View()),
		vpStyle.Render(m.viewport.View()),
	)
	return tea.NewView(lipgloss.JoinVertical(lipgloss.Left, body, m.footerView()))
}
```

## Common mistakes

- **Pointer vs. value receivers.** `layout` uses a pointer receiver (`*model`) so it can change `m`. `Update` uses a value receiver, so it changes its own copy and returns that copy. That's fine as long as you return `m`. Problems start when you mix the two styles inconsistently.
- **Ignoring style frames.** If you give a child the full terminal size and then wrap it in a border, every line is 2 columns too wide. Lipgloss then wraps those lines, which also looks garbled. Always subtract `GetFrameSize()`.
- **Calling `SetContent` in `Init` or the constructor.** The width isn't known yet at that point, so the content gets wrapped or truncated wrong. Do it in `layout()`.
- **Hard-coded heights.** Measure headers and footers with `lipgloss.Height(...)` rather than assuming they're one line tall.
- **v1 API leftovers.** In v2 the viewport uses `SetWidth` and `SetHeight` (or `viewport.New(viewport.WithWidth(w), viewport.WithHeight(h))`) instead of the `Width`/`Height` fields. `View()` returns a `tea.View` instead of a string. Check these method names against the Bubbles version you have installed.

If you paste your model's `Update`, `View` and constructor, I can show you exactly where the size is getting lost.
