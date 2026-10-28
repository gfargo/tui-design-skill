You don't have a sizing bug. Your children just have no size yet. A Bubble Tea program starts before it knows the terminal size, and Bubbles components never read `tea.WindowSizeMsg` themselves. Until you set their size, the `list` is zero-sized and renders a broken fragment, and the `viewport` has height 0 and renders nothing. Resizing "fixes" it only because that's when your code first sets their sizes.

The fix has three parts:

1. **Store the size from `tea.WindowSizeMsg`** in the parent model, then pass it to every child through one `layout()` function.
2. **Return a placeholder from `View` until that message arrives**, so you never render zero-sized children.
3. **Subtract the space your borders, padding and status bar take** before sizing the children. In Lipgloss v2, `Width`/`Height` *include* border and padding, so the size you give a child must leave room for its frame.

```go
var pane = lipgloss.NewStyle().BorderStyle(lipgloss.RoundedBorder()).Padding(0, 1)

const statusH = 1

type model struct {
    width, height int
    list          list.Model
    viewport      viewport.Model
    focus         int // 0 = list, 1 = viewport
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmd tea.Cmd
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height
        m.layout()
        return m, nil
    case tea.KeyPressMsg:
        // Send keys to the focused child only, or both will scroll.
        if m.focus == 0 {
            m.list, cmd = m.list.Update(msg)
        } else {
            m.viewport, cmd = m.viewport.Update(msg)
        }
        return m, cmd
    }
    // Pass other messages (filter results, etc.) on to the list.
    m.list, cmd = m.list.Update(msg)
    return m, cmd
}

// One place that turns the window size into child sizes.
func (m *model) layout() {
    hFrame := pane.GetHorizontalBorderSize() + pane.GetHorizontalPadding()
    vFrame := pane.GetVerticalBorderSize() + pane.GetVerticalPadding()
    bodyH := m.height - statusH

    listW := m.width / 3
    m.list.SetSize(listW-hFrame, bodyH-vFrame)
    m.viewport.SetWidth(m.width - listW - hFrame) // v2 setters, not fields
    m.viewport.SetHeight(bodyH - vFrame)
    // If you pre-wrap content to the viewport width, call SetContent again here.
}

func (m model) View() tea.View {
    if m.width == 0 { // no WindowSizeMsg yet: every child is zero-sized
        return tea.NewView("loading…")
    }
    listW := m.width / 3
    bodyH := m.height - statusH
    body := lipgloss.JoinHorizontal(lipgloss.Top,
        pane.Width(listW).Height(bodyH).Render(m.list.View()),
        pane.Width(m.width-listW).Height(bodyH).Render(m.viewport.View()),
    )
    v := tea.NewView(body + "\n" + m.statusLine())
    v.AltScreen = true
    return v
}
```

**Other things that cause the same symptom:**
- **Lost size updates.** If you call `m.list.Update(msg)` without assigning the result back, or set sizes in a helper with a value receiver, the size never sticks. `layout()` takes `*model` for this reason.
- **v1 habits.** `m.viewport.Width = n` or `viewport.New(w, h)` won't compile in v2. Use `SetWidth`/`SetHeight` and `viewport.New(viewport.WithWidth(w), viewport.WithHeight(h))`. The list already used `SetSize`.
- **Hardcoded sizes at construction.** `viewport.New(viewport.WithWidth(80), …)` in your constructor hides the bug at 80 columns and breaks at every other size. Let `layout()` own sizing.
- **Lipgloss v1 math.** In v1, `Width(20)` plus a border rendered 22 columns wide. In v2 it renders exactly 20. If you used to add the border on top, your panes will now be too small or wrap.

**Small terminals:** a 1/3 + 2/3 split falls apart in a 60-column tmux split, where the list gets about 16 usable columns. Branch in `layout()` and `View()`:

```
≥ 80 cols                       < 80 cols (single pane, Tab/Enter swaps)
╭─ list ──╮╭─ preview ───────╮  ╭─ list ─────────────────────╮
│ › item1 ││ content…        │  │ › item1                    │
│   item2 ││                 │  │   item2                    │
╰─────────╯╰─────────────────╯  ╰────────────────────────────╯
 status                          status · enter: preview
```

Below about 40×10, show a plain "terminal too small (need 40×10)" message instead of shrinking the children to nothing.

**Testing:** send a `tea.WindowSizeMsg{Width: 80, Height: 24}` into `Update` and check the list and viewport sizes. Also golden-test `View()` at 80×24, at 60 columns, and before any size message arrives, so the placeholder path stays covered.
