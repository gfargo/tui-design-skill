The cause is that a Bubble Tea program starts with no size, and Bubbles never read `tea.WindowSizeMsg` themselves. Until your parent model calls `SetSize` on the children, the list is zero-sized and draws a broken fragment, and the viewport is zero-sized and draws nothing. Resizing fixes it because by then something finally calls `SetSize`.

The fix:

1. **Store the size in the parent.**
2. **Size every child from one `layout()` function.**
3. **Show a placeholder from `View` until the first size arrives.**

## The pattern (v2 APIs)

```go
type model struct {
    list          list.Model
    viewport      viewport.Model
    width, height int
    showDetail    bool // narrow mode: viewport replaces the list
}

const minW, minH = 40, 8 // your real floor, not a guess

var paneStyle = lipgloss.NewStyle().Border(lipgloss.RoundedBorder())

func (m *model) layout() {
    bodyH := m.height - 1 // one-line status bar
    fx, fy := paneStyle.GetFrameSize()

    if m.width >= 80 { // split: list | viewport
        leftW := m.width / 3
        m.list.SetSize(leftW-fx, bodyH-fy)
        m.viewport.SetWidth(m.width - leftW - fx)
        m.viewport.SetHeight(bodyH - fy)
    } else { // narrow: one pane at a time, full width
        m.list.SetSize(m.width-fx, bodyH-fy)
        m.viewport.SetWidth(m.width - fx)
        m.viewport.SetHeight(bodyH - fy)
    }
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height
        m.layout()
        return m, nil
    case detailLoadedMsg:
        m.viewport.SetContent(msg.text) // update the existing viewport; don't rebuild it
        m.viewport.GotoTop()
    }
    // ...route keys to the focused child, as before
}

func (m model) View() tea.View {
    var s string
    switch {
    case m.width == 0: // no WindowSizeMsg yet
        s = "loading…"
    case m.width < minW || m.height < minH:
        s = fmt.Sprintf("terminal too small: need %dx%d\nresize, or press q to quit", minW, minH)
    default:
        s = m.render()
    }
    v := tea.NewView(s)
    v.AltScreen = true
    return v
}
```

## Things that commonly cause "fixed only after resize"

Even if you already handle `WindowSizeMsg`, check for these:

- **Rebuilding a child after sizing.** For example, `m.viewport = viewport.New()` in a data-loaded handler replaces the sized viewport with a zero-sized one. Call `SetContent` on the existing viewport instead. If you really must rebuild it, call `m.layout()` right after.
- **Sizing only some children.** For example, only the focused child, or only inside `if !m.ready`. Every child should be sized on every size message.
- **v1 Lipgloss border math.** In Lipgloss v2, `Width` and `Height` include the border and padding. Old code like `Width(w-2)` makes panes 2 cells too narrow, and the overflow wraps into a garbled frame. Subtract `GetFrameSize()` from the child's size, as above, and don't subtract it again from the pane style.
- **Layout changes that aren't resizes.** Toggling full help, showing an error line, or entering narrow mode all change the space available. Call `m.layout()` from those places too, not only on `WindowSizeMsg`.
- **v1 field assignments.** `m.viewport.Width = …` is now `SetWidth`/`SetHeight`. The list has always used `SetSize`.

## Smaller terminals

- **80×24:** the list takes a third and the viewport gets the rest. Use the single status line for key hints, not a second bordered footer.
- **60 columns (tmux split):** one pane at a time. The list wins; Enter opens the viewport full-width and Esc goes back. Don't squeeze two 28-column panes side by side.
- **Below `minW`×`minH`:** show the "too small" message, which names the size it needs, and keep `q`/Ctrl+C working. Never render a broken frame.

## Lock it in with tests

The cheapest test feeds `tea.WindowSizeMsg{Width: 60, Height: 24}` to `Update` and asserts that `m.list.Width()` and `m.viewport.Height()` are non-zero and correct. Then add golden-frame tests with teatest (`github.com/charmbracelet/x/exp/teatest/v2`), using `WithInitialTermSize` at 80×24, 60×24, and your minimum. Pin `tea.WithColorProfile(colorprofile.ASCII)` so the goldens don't flap. Also send a size message partway through a run to check that the layout reflows instead of keeping the startup size.

If you paste your `Update` and `View`, I can find exactly where the size is getting lost.
