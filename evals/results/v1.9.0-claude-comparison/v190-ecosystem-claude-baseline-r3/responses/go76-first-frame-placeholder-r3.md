There's no Go code in this directory, so this answer is based on how Bubble Tea v2 normally behaves rather than on your code. The symptoms you describe usually have one cause.

## What's going on

Bubble Tea calls `View()` before it knows the terminal size. The size comes later, as a `tea.WindowSizeMsg`. Until then your list and viewport have width and height 0 (or whatever you passed to `list.New`/`viewport.New`). That means:

- the **list** lays out pagination and items in a 0×0 box, so you get a garbled fragment
- the **viewport** has height 0, so it shows nothing. If you called `SetContent` before it had a size, it may also look empty until something forces it to recalculate.

Resizing fixes it only because that sends another `WindowSizeMsg`. The question is whether your code handles that message correctly the first time.

## The approach

1. **Keep the size in the parent model** and lay out every child from it.
2. **Don't render the real UI until you have a size.** Use a `ready` flag.
3. **Compute each child's size from what's around it.** Measure the header and footer with `lipgloss.Height`, and subtract border and padding with `style.GetFrameSize()`.
4. **Call the children's setters yourself.** `list.Model` doesn't resize itself from `WindowSizeMsg`. You have to call `SetSize`.
5. **Set or re-wrap viewport content after sizing it**, and do it again on every resize if the content depends on width.

```go
type model struct {
    list     list.Model
    vp       viewport.Model
    ready    bool
    w, h     int
    content  string
}

var paneStyle = lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).Padding(0, 1)

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmds []tea.Cmd

    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.w, m.h = msg.Width, msg.Height
        m.layout()
        m.ready = true
    }

    var cmd tea.Cmd
    m.list, cmd = m.list.Update(msg) // assign the result back, or the state is lost
    cmds = append(cmds, cmd)
    m.vp, cmd = m.vp.Update(msg)
    cmds = append(cmds, cmd)

    return m, tea.Batch(cmds...)
}

func (m *model) layout() {
    headerH := lipgloss.Height(m.headerView())
    footerH := lipgloss.Height(m.footerView())
    bodyH := m.h - headerH - footerH

    fw, fh := paneStyle.GetFrameSize()
    listW := m.w / 3
    vpW := m.w - listW

    m.list.SetSize(listW-fw, bodyH-fh)
    m.vp.SetWidth(vpW - fw)
    m.vp.SetHeight(bodyH - fh)
    m.vp.SetContent(wrap(m.content, vpW-fw)) // re-wrap for the new width
}

func (m model) View() tea.View {
    if !m.ready {
        return tea.NewView("Loading…")
    }
    body := lipgloss.JoinHorizontal(lipgloss.Top,
        paneStyle.Render(m.list.View()),
        paneStyle.Render(m.vp.View()),
    )
    v := tea.NewView(lipgloss.JoinVertical(lipgloss.Left, m.headerView(), body, m.footerView()))
    v.AltScreen = true
    return v
}
```

## Common mistakes that cause exactly your symptoms

- **Ignoring the result of a child's `Update`.** Writing `m.list.Update(msg)` without `m.list, cmd = ...` throws the change away.
- **Handling `WindowSizeMsg` only inside a child model** that the parent never forwards the message to. This also happens when the child is on a screen that isn't active when the message arrives. Store the size in the parent, and call `layout()` again whenever you create or switch to a child.
- **A pointer-receiver `layout()` called from a value-receiver `Update`.** That's fine as long as you return the same `m` you changed, as in the example above.
- **Not subtracting the frame size.** If a border or padding makes the rendered width bigger than the terminal, lines wrap and the layout looks garbled even after resizing.
- **Calling `SetContent` once in `Init` or the constructor**, before the viewport has a width. Call it again in `layout()`.

If you paste your model's `Update` and `View`, I can point to the exact line that's causing it.
