**No. For a new app, use Bubble Tea v2 with Lipgloss and Bubbles. Copy lazygit's interaction design, not its library.**

## Why not gocui

- **lazygit no longer uses a gocui you can depend on.** In April 2026 it copied its fork into its own repo as `lazygit/pkg/gocui` and moved to tcell v3. The `jesseduffield/gocui` fork is effectively retired.
- **The maintained upstream has gone quiet.** That's `awesome-gocui/gocui`. Its last release was v1.1.0 in 2022, and it's still on tcell v2.
- **You'd be building the hard parts yourself.** gocui gives you named views that you write text into, plus per-view keybindings. Lists, filtering, help footers, text inputs and tests are all on you. Bubble Tea's ecosystem already has them: `list`, `viewport`, `textinput`, `help`/`key`, and teatest plus golden-file rendering tests.

**When gocui still makes sense:** you're maintaining an existing gocui app, or you specifically want its model where each panel is a text buffer you write to. If you need lots of widgets (forms, tables, trees), **tview** is the other option; k9s uses it.

## The lazygit parts worth copying

- **Panels stay put.** Five or so panels in fixed positions, `1`–`9` jumps to a panel, `Tab` cycles through them.
- **Letters depend on the panel.** `c` can mean commit in Files and checkout in Branches.
- **A footer always shows what each key does right now.** That's what makes context-dependent letters usable. Without the footer, don't try this pattern.
- **Tabs inside panels.** `[`/`]` switches sub-tabs, like Local / Remotes / Tags under Branches.
- **`$EDITOR` handoff.** Use `tea.ExecProcess`, and reload your data in its callback. Repainting alone shows stale state.

## Layout at full width and at the floor

```
120+ cols
+-[1] Status---------+-Diff--------------------------------------+
| ✓ main ↑2          | @@ -12,7 +12,9 @@                         |
+-[2] Files----------+ - old line                                |
| > M  cmd/root.go   | + new line                                |
|   A  pkg/ui.go     |                                           |
+-[3] Branches-------+                                           |
|   main  feat/x     |                                           |
+-[4] Commits--------+                                           |
|   a1b2c3 fix parse |                                           |
+--------------------+-------------------------------------------+
 c commit · a stage all · Enter open · / filter · ? help · q quit

60 cols: one panel at a time
+-[2/5] Files ---------------------------+
| > M  cmd/root.go                       |
|   A  pkg/ui.go                         |
+----------------------------------------+
 1-5 panel · Enter diff · Esc back · ? help
```

**Floor behavior:**
- **About 120 columns and up:** sidebar plus main panel. Size the sidebar at 25–30% of the width, between 20 and 40 columns.
- **80×24:** keep both, but squeeze the sidebar to 30 columns. With four or more panels stacked, each one gets about 4 rows. Collapse the ones that aren't focused to just their title line, so the focused one gets the height.
- **60 columns:** show one panel full-width. `Enter` opens the diff and `Esc` goes back. The `[2/5]` in the title says where you are.
- **Below your real minimum** (say 60×12): show "terminal too small, needs 60×12." Don't draw a broken layout.

**Clutter check:**
- Use one border level per panel and never put a border inside a panel.
- Don't show focus with border color alone. Also make the title bold or add a marker, so it still reads under `NO_COLOR`.
- A `>` marker should appear only on the selected row. If every row has one, it means nothing.
- Keep the footer to the 5–7 keys that matter in the current panel, and put the rest behind `?`.

## Bubble Tea skeleton

```go
type pane int
const (paneStatus pane = iota; paneFiles; paneBranches; paneCommits; paneCount)

type model struct {
    focus         pane
    panes         [paneCount]list.Model
    diff          viewport.Model
    width, height int
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height
        m = m.layout() // pick the width band, call SetSize on every child
    case tea.KeyPressMsg:
        if m.panes[m.focus].FilterState() != list.Filtering { // "q" and "2" are filter text otherwise
            switch s := msg.String(); s {
            case "q":
                return m, tea.Quit
            case "1", "2", "3", "4":
                m.focus = pane(s[0] - '1')
                return m, loadDiff(m.selected()) // git runs in a Cmd, never in Update
            }
        }
    }
    var cmd tea.Cmd
    m.panes[m.focus], cmd = m.panes[m.focus].Update(msg)
    return m, cmd
}
```

Some details that often bite:
- **Before the first `WindowSizeMsg`:** have `View()` return a placeholder. Bubbles components don't size themselves.
- **Quit keys:** call `DisableQuitKeybindings()` on each list so your parent model owns quitting, and handle `ctrl+c` and `ctrl+z` (`tea.Suspend`) globally.
- **Lipgloss v2 sizing:** `Width`/`Height` now include the border, so v1-style `Width(w-2)` math comes out 2 cells too narrow.
- **Text width:** measure with `lipgloss.Width()`, not `len()`.
- **Tests:** unit-test `Update` with `tea.KeyPressMsg` literals, then golden-test rendered frames at 120×40, 80×24 and 60×24. Pin the color profile with `tea.WithColorProfile(colorprofile.ASCII)` so the golden files don't vary from machine to machine.

If you tell me the domain (Kubernetes, CI, a database…), I can sketch the actual panels and the letter keys for each one.
