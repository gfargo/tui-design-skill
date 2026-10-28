**Short answer: no. Use Bubble Tea v2 with Lipgloss and Bubbles, and copy lazygit's interaction design rather than its library.**

## Why not gocui

- **The fork lazygit used is retired.** In April 2026 lazygit copied `jesseduffield/gocui` into its own repo as `pkg/gocui` and moved to tcell v3. "Use what lazygit uses" now means depending on code inside another app's repo.
- **The maintained upstream is stale.** `awesome-gocui/gocui` last released v1.1.0 in 2022 and is still on tcell v2. You would get no newer keyboard protocol support (e.g. a Shift+Enter that actually arrives), no compositor for overlays, and no test harness.
- **What makes lazygit good doesn't come from gocui.** It's the interaction model: fixed numbered panels, `1`–`5` to jump between them, `Tab` to cycle, single letters that do different things per panel, `[`/`]` sub-tabs, confirmation popups, undo, a command log, and a footer that always shows what each key does right now. You can build all of that on Bubble Tea.

**When gocui still makes sense:** you're maintaining an existing gocui app, or you specifically want its model, where each view is a buffer you `Fprintln` into and a manager function sets view positions on every redraw. Even then, use `awesome-gocui/gocui`, not the jesseduffield fork.

**When to pick tview instead:** you need lots of ready-made widgets side by side (forms, trees, tables) and prefer callbacks to message passing. k9s is built on tview.

## What you take on with Bubble Tea

- **No layout engine.** You compute pane sizes from `tea.WindowSizeMsg` and join them with `lipgloss.JoinHorizontal` / `JoinVertical`. In Lipgloss v2, `Width`/`Height` include the border and padding, so old `Width(w-2)` math from v1 examples comes out 2 cells too narrow.
- **You route focus yourself.** Single-letter keys go to the focused pane. While a filter or text input has focus, `q` and `1`–`5` are typed text, not commands.
- **Popups** use Lipgloss layers: `lipgloss.NewLayer(...).Z(1)` plus `NewCompositor`. Modifier keys like Ctrl+C stay global.

A skeleton of the routing (v2 APIs):

```go
type pane int
const (statusPane pane = iota; filesPane; branchesPane; commitsPane; stashPane)

type model struct {
    focus         pane
    panes         [5]list.Model
    main          viewport.Model
    width, height int
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height
        m.layout() // recompute every pane's size; Bubbles never read the size themselves
        return m, nil
    case tea.KeyPressMsg:
        switch s := msg.String(); s {
        case "ctrl+c":
            return m, tea.Quit
        case "ctrl+z":
            return m, tea.Suspend // Bubble Tea doesn't bind this for you
        }
        if m.panes[m.focus].FilterState() != list.Filtering {
            switch s := msg.String(); s {
            case "q":
                return m, tea.Quit
            case "1", "2", "3", "4", "5":
                m.focus = pane(s[0] - '1')
                return m, nil
            case "tab":
                m.focus = (m.focus + 1) % 5
                return m, nil
            }
        }
    }
    var cmd tea.Cmd
    m.panes[m.focus], cmd = m.panes[m.focus].Update(msg) // panel-specific letters live here
    return m, cmd
}
```

Run every git or subprocess call as a `tea.Cmd`, never inside `Update`. Use `tea.ExecProcess` to hand the terminal to `$EDITOR`, and reload data in its callback, because repainting alone shows the old state.

## Layout at each width

Wide (120+ columns): the full lazygit layout.

```
┌ 1 Status ──────┐┌ Diff ───────────────────────────────┐
│ main → origin  ││ @@ -12,4 +12,6 @@                    │
┌ 2 Files ───────┐│ + added line                         │
│ M app.go       ││                                      │
┌ 3 Branches ────┐│                                      │
┌ 4 Commits ─────┐│                                      │
┌ 5 Stash ───────┐└──────────────────────────────────────┘
 c commit  p push  space stage  ? help         ⟳ fetching
```

80×24: five stacked panels only get about 4 rows each, which is unusable. Make it an accordion: the focused sidebar panel expands and the others shrink to their title row. The diff stays on the right.

60 columns (a tmux split), single pane:

```
┌ 2 Files ─────────────── 1 2 3 4 5 ┐
│ M app.go                          │
│ A ui/panes.go                     │
└───────────────────────────────────┘
 enter diff  space stage  ? help
```

At this width, `1`–`5` swap which panel fills the screen, `Enter` opens the diff full-width, and `Esc` goes back. Below about 60×16 (pick yours from what must stay usable), show a "terminal too small, need 60×16" message instead of a broken layout.

## Avoiding clutter

- **One level of border only.** Don't nest boxes inside the panel frames.
- **Show focus once.** A highlighted border with the number in the title is enough. Don't also add a `▶` marker, inverse title, and bold text.
- **Never cut the footer hint bar.** Letters that mean different things in each panel only work because the footer shows what they do right now.

## Tests

- Unit-test `Update` with `tea.KeyPressMsg` literals. Cover focus switching and that `q` while filtering goes into the filter instead of quitting.
- Golden-test rendered frames at 120×40, 80×24, and 60×24 with `tea.WithColorProfile(colorprofile.ASCII)`. Without a pinned color profile the goldens change between terminals.

If you tell me what the tool manages (git, containers, CI…), I can sketch the panel list and per-panel keys.
