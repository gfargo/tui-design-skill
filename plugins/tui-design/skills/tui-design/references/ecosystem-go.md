# Go ecosystem — Bubble Tea, tview, gocui, Cobra

Go TUIs split into two camps: the **Charm stack** (Bubble Tea + Lipgloss + Bubbles + Huh) for new projects, and **tcell + tview** for widget-rich apps. **gocui** is a third, legacy lineage behind lazygit (now an in-tree fork) and lazydocker. CLI framing comes from **Cobra** (kubectl, gh, hugo, helm, docker), `urfave/cli` or Kong.

**Contents:**
- [Quick recommendation](#quick-recommendation)
- [Bubble Tea](#bubble-tea-charmbraceletbubbletea) — [Lifecycle and terminal handoff](#lifecycle-and-terminal-handoff) · [Lipgloss](#lipgloss-charmbraceletlipgloss) · [Bubbles](#bubbles-charmbraceletbubbles) · [Huh](#huh-charmbracelethuh)
- [Other Charm libraries](#other-charm-libraries-worth-knowing)
- [tview](#tview-rivotview) · [gocui](#gocui-awesome-gocuigocui) · [tcell](#lower-level-tcell)
- [CLI framing and output: Cobra, urfave/cli, pretty output](#cli-framing-cobra-and-urfavecli)
- [Testing](#testing) · [Debugging](#debugging) · [Cross-platform notes](#cross-platform-notes)

## Quick recommendation

| If the user wants… | Use |
|---|---|
| Modern TUI with clean architecture and Charm aesthetic | **Bubble Tea + Lipgloss + Bubbles** |
| Multi-pane vim-keybinding "lazy*"-style app | **Bubble Tea + Lipgloss** (compose the panes yourself); **gocui** (`awesome-gocui/gocui`) only for its exact views-as-buffers model |
| Heavy data exploration with tables, trees, forms | **tview** (callback-style, retained-mode) |
| One-shot fancy CLI prompts only | **Huh** (Go form library) or **gum** (shell wrapper) |
| TUI served over SSH | **Wish** (wraps Bubble Tea apps as SSH server) |

**Default choice for new projects: Bubble Tea + Lipgloss + Bubbles + Cobra.** (`gh` is a Cobra CLI, not a full-screen TUI: Lipgloss and Glamour for output, Charm v2 Bubble Tea, Bubbles, and Huh for prompts.)

---

## Bubble Tea (charmbracelet/bubbletea)

The Elm Architecture in Go, and the most widely used Go TUI framework: `Model → Update(Msg) → (Model, Cmd) → View() tea.View`.

**v2 is stable** (v2.0.0 shipped February 2026 after betas/RCs through 2025; current is v2.1.x, and Go 1.26+ is required since v2.0.10). v2.1.0 (October 2026) is additive: `View.ProgramStatus` reports idle/working/blocked/done/error to terminals that support OSC 7501 program-status reporting. The status is not cleared on exit, so report Done, Error, or Idle before quitting rather than leaving working or blocked behind ([`tea.go`](https://github.com/charmbracelet/bubbletea/blob/v2.1.0/tea.go)). What changed and why it matters:
- **New renderer** — Bubble Tea now owns terminal I/O and Lipgloss became pure (no more I/O fights between the two).
- **Progressive keyboard enhancements** — with the Kitty protocol you can finally bind `shift+enter`, `ctrl+i` distinct from `tab`, `super+space`, etc. Always keep a legacy fallback: `tea.KeyboardEnhancementsMsg` arrives only if the terminal answers (possibly after the first frame), so accept `shift+enter` and a fallback such as `ctrl+j` always, but show the `shift+enter` hint only once `msg.SupportsKeyDisambiguation()` is true.
- **Import path moved** to `charm.land/bubbletea/v2`. All Charm v2 libraries import from `charm.land/<name>/v2` — bubbletea, bubbles, lipgloss, huh, wish, glamour, log, fang — keep them on the same major. Lower-level pieces (`colorprofile`, `ultraviolet`, `x/*`) stay on `github.com/charmbracelet/...` paths.

**Migrating v1 → v2:** the MVU shape survives, but every model gets touched, so start new projects on v2. What breaks layouts and compiles ([Bubbles upgrade guide](https://github.com/charmbracelet/bubbles/blob/v2.2.1/UPGRADE_GUIDE_V2.md)):

| Area | v1 | v2 |
|---|---|---|
| Bubble Tea | `View() string`, `tea.KeyMsg`, `tea.WithAltScreen()` | `View() tea.View`, `tea.KeyPressMsg`, `v.AltScreen = true` |
| Lipgloss sizing | `Width`/`Height` exclude the border | they include border and padding (see Lipgloss) |
| Lipgloss color | `AdaptiveColor`, `SetColorProfile` | `LightDark`; print with `lipgloss.Println` |
| Bubbles sizing | `m.Width = n`; `viewport.New(w, h)` | `m.SetWidth(n)` / `m.Width()`; `viewport.New(viewport.WithWidth(w), viewport.WithHeight(h))` |
| Bubbles keymaps | `textinput.DefaultKeyMap` (var) | `DefaultKeyMap()` (func; also `paginator`, `textarea`) |
| Bubbles styles | `list.DefaultStyles()`, auto-adapting colors | `help.DefaultStyles(isDark)`, `list.DefaultStyles(isDark)`, `list.NewDefaultItemStyles(isDark)` |
| Bubbles constructors | `NewModel()` | `New()` |

The setter change covers `filepicker`, `help`, `progress`, `table`, `textinput`, and `viewport`; `list` already used `SetSize`.

**The mental model:** one `Model` struct holds all state and `Init` returns the first Cmd (or `nil`). `Update(msg)` is the only place state changes. `View()` returns the whole frame as a `tea.View` (content plus alt screen, mouse mode, cursor), which Bubble Tea diffs into minimal ANSI. Side effects live in `tea.Cmd`s whose messages return through `Update`.

```go check=go/counter
type model struct {
    count int
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyPressMsg:  // KeyMsg is an interface in v2; msg.Code/msg.Text replace Type/Runes
        switch msg.String() {
        case "q", "ctrl+c":
            return m, tea.Quit
        case "+", "right", "l":
            m.count++
        case "-", "left", "h":
            m.count--
        }
    }
    return m, nil
}

func (m model) View() tea.View {
    v := tea.NewView(fmt.Sprintf("Count: %d\n\nq quit · ←/→ change", m.count))
    v.AltScreen = true  // don't pollute scrollback; required for full-screen TUIs
    return v
}

func main() {
    p := tea.NewProgram(model{})
    if _, err := p.Run(); err != nil {
        log.Fatal(err)
    }
}
```

`Program.Run()` owns Bubble Tea's normal terminal cleanup and default panic recovery. Do not add `defer p.RestoreTerminal()` as a final-cleanup guard: `RestoreTerminal` is the counterpart to `ReleaseTerminal` and resumes Bubble Tea's terminal modes rather than restoring the user's shell. Add an outer custom cleanup boundary only when deliberately bypassing or disabling the framework-managed path.

### Lifecycle and terminal handoff

Bubble Tea v2 owns the terminal for the whole `Program.Run()` call. Keep resumable work inside that lifecycle rather than tearing the program down and trying to reconstruct it.

| Boundary | Bubble Tea v2 contract |
|---|---|
| Normal exit | Return `tea.Quit`. `Program.Run()` performs final restoration on normal, error, and recovered-panic paths. |
| Interrupt or termination | Raw-mode Ctrl+C arrives as `tea.KeyPressMsg`; return `tea.Interrupt` when the caller should receive `tea.ErrInterrupted`, or `tea.Quit` for an intentional zero-status quit. Bubble Tea's default signal handler turns external SIGINT/SIGTERM into managed termination. Do not call `os.Exit` from `Update`. |
| Interactive child | Return `tea.ExecProcess(exec.Command(...), callback)`. It pauses the program, releases the terminal, attaches the child's standard streams, waits, restores and repaints, then reports the child error (or, after child success, a restoration error) through the callback message. In that callback, reload data the child could have changed; repainting alone uses the old model. Use an ordinary `tea.Cmd` for non-interactive I/O. |
| Foreground suspend | Bubble Tea never binds Ctrl+Z for you: return `tea.Suspend` from your own `"ctrl+z"` key-press case (see the key-routing sample under Bubbles). After the Unix job resumes, handle `tea.ResumeMsg` to reload state that changed while away. Suspend is unsupported on Windows, so never require it. |

`Program.ReleaseTerminal()` / `RestoreTerminal()` is a temporary handoff escape hatch. Prefer [`ExecProcess`](https://github.com/charmbracelet/bubbletea/blob/v2.1.0/exec.go) for editors and shells; Bubble Tea's [tagged lifecycle source](https://github.com/charmbracelet/bubbletea/blob/v2.1.0/tea.go) defines signal, interrupt, suspend, and restoration semantics together.

**Frame-level declarations live on the view, not the program.** `tea.WithAltScreen()`, `tea.WithMouseCellMotion()`, and `tea.WithMouseAllMotion()` were removed in v2 — set `v.AltScreen = true` and `v.MouseMode = tea.MouseModeCellMotion` (or `tea.MouseModeAllMotion` for hover) in `View()`. Inline is the default, and because these fields are read every frame, an app can switch between inline and the alternate screen at runtime. **Important options:** `tea.WithInput(reader)` / `tea.WithOutput(writer)` (testing, Wish) and `tea.WithColorProfile(p)` (force a color profile, e.g. golden-file tests).

**Async via Cmds:**
```go check=go/fetch-cmd
func fetchData() tea.Msg {
    resp, err := http.Get(url)
    if err != nil { return errMsg{err} }
    defer resp.Body.Close()
    body, err := io.ReadAll(resp.Body) // *http.Response is not the data
    if err != nil { return errMsg{err} }
    return dataMsg{body}
}

// In Update, when you want to fetch:
return m, fetchData
```

`tea.Cmd` is `func() tea.Msg`. The runtime calls them in goroutines and routes the returned `Msg` back through `Update`. **Never block in `Update`** — anything I/O goes in a Cmd. Use `tea.Batch(cmds...)` for parallel commands and `tea.Sequence(cmds...)` for ordered ones.

**Pitfalls:**
- `len(string)` ≠ display width. Use `lipgloss.Width()`, which handles CJK/emoji via `charmbracelet/x/ansi` grapheme clustering.
- Goroutines never call `View()` directly — send via `program.Send(msg)`.
- Don't `fmt.Println` while the program runs. For permanent lines above an inline UI, return `tea.Println(...)`/`tea.Printf(...)` (no-ops on the alt screen); for diagnostics, see **Debugging**.

---

## Lipgloss (charmbracelet/lipgloss)

CSS-in-Go declarative styling — immutable `Style` values rendered to ANSI strings. The companion to Bubble Tea, but usable standalone.

```go check=go/lipgloss-style
var titleStyle = lipgloss.NewStyle().
    Bold(true).
    Foreground(lipgloss.Color("#FAFAFA")).
    Background(lipgloss.Color("#7D56F4")).
    Padding(0, 1).
    BorderStyle(lipgloss.RoundedBorder()).
    BorderForeground(lipgloss.Color("63"))

lipgloss.Println(titleStyle.Render("Hello, world")) // downsamples for the terminal; fmt.Println would not
```

**Layout helpers:** `lipgloss.JoinHorizontal(lipgloss.Top, left, right)` (side-by-side), `lipgloss.JoinVertical(lipgloss.Left, a, b, c)` (stacked), `lipgloss.Place(width, height, hPos, vPos, content)` (center/anchor in a box), and `lipgloss.Width(s)` / `lipgloss.Height(s)` (measure rendered output, skipping ANSI and counting wide graphemes).

**Sizing:** in v2, `Width`/`Height` are the total block size, border and padding included (`// Include borders in block size` in [`style.go`](https://github.com/charmbracelet/lipgloss/blob/v2.0.6/style.go)). In v1 the border sat outside ([v1.1.0](https://github.com/charmbracelet/lipgloss/blob/v1.1.0/style.go)), so carried-over math such as `Width(w - 2)` for a bordered pane now comes out 2 cells too narrow. Margins stay outside. Text wraps at `Width` minus border and padding.

```go check=go/lipgloss-block-size
box := lipgloss.NewStyle().
    Width(20).Height(5).
    Padding(0, 1).
    BorderStyle(lipgloss.RoundedBorder())

out := box.Render("hello") // lipgloss.Width(out) == 20, lipgloss.Height(out) == 5; v1 gave 22x7
inner := 20 - box.GetHorizontalBorderSize() - box.GetHorizontalPadding() // 16 text columns
```

**No flexbox.** You compute widths from the cached `tea.WindowSizeMsg`:

```go check=go/window-size
case tea.WindowSizeMsg:
    m.width, m.height = msg.Width, msg.Height
    m.leftPaneWidth = msg.Width / 3
    m.rightPaneWidth = msg.Width - m.leftPaneWidth
```

**Overlays and hit-testing.** Draw layers: `lipgloss.NewLayer(s).ID("dialog").X(x).Y(y).Z(1)`, then `lipgloss.NewCompositor(layers...).Render()` is the frame. `Compositor.Hit(x, y)` returns the top-most layer *with an ID* at a cell, so ID every layer a click can land on. `Z` is compared as written, not added to the parent's (despite the doc comment), and ties have no defined order, so use distinct values. Size the base layer to the window; an overhanging layer grows the frame. `v.OnMouse` runs against the last drawn frame, so its closure can query the compositor built in that `View`; `Update` still gets the raw `MouseClickMsg`, so handle each click in one place.

```go check=go/overlay
func (m model) View() tea.View {
    base := lipgloss.NewStyle().Width(m.width).Height(m.height).Render(m.body)
    layers := []*lipgloss.Layer{lipgloss.NewLayer(base).ID("base")}
    if m.dialog != "" {
        box := dialogStyle.Render(m.dialog)
        x, y := (m.width-lipgloss.Width(box))/2, (m.height-lipgloss.Height(box))/2
        layers = append(layers, lipgloss.NewLayer(box).ID("dialog").X(x).Y(y).Z(1))
    }
    comp := lipgloss.NewCompositor(layers...)
    v := tea.NewView(comp.Render())
    v.MouseMode = tea.MouseModeCellMotion
    v.OnMouse = func(msg tea.MouseMsg) tea.Cmd {
        if c, ok := msg.(tea.MouseClickMsg); ok {
            id := comp.Hit(c.X, c.Y).ID() // "" when no layer with an ID is there
            return func() tea.Msg { return hitMsg(id) }
        }
        return nil
    }
    return v
}
```

**Light/dark theming:** Lipgloss v2 is pure — it never touches the terminal, so *your app* queries the background once and picks variants. Standalone (no Bubble Tea running):
```go check=go/light-dark
hasDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)
lightDark := lipgloss.LightDark(hasDark)
fg := lightDark(lipgloss.Color("#236"), lipgloss.Color("#cef"))
```
Inside a running Bubble Tea program, don't call `HasDarkBackground`: its terminal query competes with Bubble Tea for input. Return `tea.RequestBackgroundColor` from `Init`, then handle `case tea.BackgroundColorMsg:` with `lipgloss.LightDark(msg.IsDark())` and rebuild your styles. Render a default palette first and treat the reply as an upgrade: it may never arrive (since v2.0.10 `tea.WithInput(nil)` skips all terminal queries, and some terminals don't answer OSC 11).
The old `AdaptiveColor` survives only in `charm.land/lipgloss/v2/compat` for migrations; prefer `LightDark` in new code.

**Sub-packages:** `lipgloss/table` (bordered tables with column alignment), `lipgloss/list` (bullet/numbered lists with custom enumerators), `lipgloss/tree` (hierarchical trees).

---

## Bubbles (charmbracelet/bubbles)

The component library for Bubble Tea. Each Bubble is itself a `tea.Model` you embed and forward messages to.

**Components shipped:**
- **`textinput`** — single-line input with placeholder, suggestions, validation. **`textarea`** — multi-line input with optional line numbers; v2.2+ adds text selection, copy/cut and word motion.
- **`list`** — virtualized list with filtering, pagination, custom delegate for row rendering. **`table`** — virtualized table with row selection (no built-in sorting; sort the rows yourself).
- **`tree`** — navigable hierarchical tree, rendered with `lipgloss/tree`. **`viewport`** — scrollable region for long content.
- **`spinner`** — prebuilt sets (`Line`, `Dot`/`MiniDot` braille, `Pulse`, …) or custom frames. **`progress`** — gradient bar with percent. **`paginator`**, **`filepicker`**, **`cursor`**, **`stopwatch`**, **`timer`**.
- **`help`** — auto-rendered footer hint bar from a `key.KeyMap`. **`key`** — declarative key bindings.

```go check=go/bubbles-embedding
type model struct {
    list list.Model
    keys keyMap
    help help.Model
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmd tea.Cmd
    m.list, cmd = m.list.Update(msg)  // forward to child
    return m, cmd
}

func (m model) View() tea.View {
    // Bubbles still return strings; the parent wraps them in a tea.View.
    return tea.NewView(m.list.View() + "\n" + m.help.View(m.keys))
}
```

**Declarative keys with `key.Binding`:**

```go check=go/key-bindings
type keyMap struct {
    Up   key.Binding
    Down key.Binding
    Quit key.Binding
}

var keys = keyMap{
    Up:   key.NewBinding(key.WithKeys("up", "k"), key.WithHelp("↑/k", "up")),
    Down: key.NewBinding(key.WithKeys("down", "j"), key.WithHelp("↓/j", "down")),
    Quit: key.NewBinding(key.WithKeys("q", "ctrl+c"), key.WithHelp("q", "quit")),
}

// In Update (tea.KeyMsg is an interface in v2 that also matches releases; switch on presses):
case tea.KeyPressMsg:
    switch {
    case key.Matches(msg, keys.Quit):
        return m, tea.Quit
    case key.Matches(msg, keys.Up):
        // ...
    }
```

**v2 sizing and styles.** Exported `Width`/`Height` fields became getter/setter pairs, and style constructors take the background. `help.New()` and `list.NewDefaultDelegate()` assume a dark background, so apply the real one when `tea.BackgroundColorMsg` arrives (see **Light/dark theming**):

```go check=go/bubbles-v2-api
m.viewport = viewport.New(viewport.WithWidth(80), viewport.WithHeight(24)) // v1: viewport.New(80, 24)
m.input = textinput.New()
m.input.SetWidth(40)                                                       // v1: m.input.Width = 40
m.input.KeyMap = textinput.DefaultKeyMap()                                 // v1: a package var

// In Update
switch msg := msg.(type) {
case tea.WindowSizeMsg:
    m.help.SetWidth(msg.Width)                   // v1: m.help.Width = msg.Width
    m.viewport.SetWidth(msg.Width)               // Width() and Height() are getters now
    m.viewport.SetHeight(msg.Height - 2)
    m.list.SetSize(msg.Width, msg.Height-2)
case tea.BackgroundColorMsg: // Init returned tea.RequestBackgroundColor
    isDark := msg.IsDark()
    m.help.Styles = help.DefaultStyles(isDark)
    m.list.Styles = list.DefaultStyles(isDark)
    d := list.NewDefaultDelegate()
    d.Styles = list.NewDefaultItemStyles(isDark)
    m.list.SetDelegate(d)
}
```

**First frame and spinners.** The program starts with no size and Bubbles never read `WindowSizeMsg` themselves: a zero-sized `list` renders a broken fragment, a zero-sized `viewport` nothing. Forward the size to every child and return a placeholder from `View` until it arrives. `spinner` has no `Init`: your `Init` must return `m.spinner.Tick` (the method value is the Cmd), and it keeps moving only while its `spinner.TickMsg` reaches `spinner.Update` and the returned Cmd is kept. `timer` and `stopwatch` have an `Init()` that starts them.

```go check=go/first-frame
func (m model) Init() tea.Cmd { return tea.Batch(m.spinner.Tick, m.timer.Init()) }

// In Update
case tea.WindowSizeMsg:
    m.width, m.height = msg.Width, msg.Height
    m.list.SetSize(msg.Width, msg.Height-1)
case spinner.TickMsg:
    m.spinner, cmd = m.spinner.Update(msg) // drop this Cmd and the spinner stops

func (m model) View() tea.View {
    if m.width == 0 { // no WindowSizeMsg yet: every child is zero-sized
        return tea.NewView("loading…")
    }
    return tea.NewView(m.spinner.View() + "\n" + m.list.View())
}
```

**Route keys to the focused child.** A global `q` handler quits while the user is typing "q" into a list's filter. Check `FilterState() == list.Filtering` before single-character global keys; modified keys (Ctrl+C, Ctrl+Z) stay global. The list also quits on `q` itself while browsing (it disables that while filtering); call `DisableQuitKeybindings()` if the parent owns quitting.

```go check=go/list-filter-keys
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    if k, ok := msg.(tea.KeyPressMsg); ok {
        switch k.String() {
        case "ctrl+c":
            return m, tea.Quit
        case "ctrl+z":
            return m, tea.Suspend // Bubble Tea does not bind this for you
        case "q":
            if m.list.FilterState() != list.Filtering { // otherwise "q" is filter text
                return m, tea.Quit
            }
        }
    }
    var cmd tea.Cmd
    m.list, cmd = m.list.Update(msg) // everything else goes to the focused child
    return m, cmd
}
```

The `help` Bubble renders the footer from these bindings: `help.View(m.keys)` needs `keyMap` to implement `help.KeyMap`:

```go check=go/help-keymap
func (k keyMap) ShortHelp() []key.Binding  { return []key.Binding{k.Up, k.Down, k.Quit} }
func (k keyMap) FullHelp() [][]key.Binding { return [][]key.Binding{{k.Up, k.Down}, {k.Quit}} }
```

**Real cursor.** `textinput` and `textarea` draw a virtual cursor (a styled cell) and leave the terminal's cursor hidden, but IME composition windows and screen readers follow the terminal cursor. For text entry call `SetVirtualCursor(false)` and set `v.Cursor = m.input.Cursor()`, adding the input's offset in the frame (`Cursor()` is relative to the input). It is nil while blurred, so blur the input when an overlay covers it. `textinput.Cursor()` counts runes, not cells (v2.2.1): each wide CJK or emoji rune leaves the caret a cell short; `textarea` counts cells.

```go check=go/real-cursor
m.input = textinput.New()
m.input.SetVirtualCursor(false) // the terminal cursor is the caret now
m.input.Focus()                 // Cursor() is nil while blurred

// In View
v := tea.NewView("Search\n" + m.input.View())
if c := m.input.Cursor(); c != nil {
    c.Y++ // one title line above the input
    v.Cursor = c
}
```

---

## Huh (charmbracelet/huh)

Forms on top of Bubble Tea, for one-shot prompts (wizards) and embeddable form panes. Huh v2 (`charm.land/huh/v2`) is built on Bubble Tea v2 — built-in themes are now `func(isDark bool) *Styles`; wrap one as a `huh.Theme` with `form.WithTheme(huh.ThemeFunc(huh.ThemeCharm))`. Huh takes `isDark` from the `tea.BackgroundColorMsg` it receives but v2.0.3 never requests one, so an embedding parent must return `tea.RequestBackgroundColor` from its own `Init` and forward the reply. A standalone `form.Run()` has no parent to ask and always renders the light variant ([huh#834](https://github.com/charmbracelet/huh/issues/834)); detect the background first (`lipgloss.HasDarkBackground(os.Stdin, os.Stdout)` is safe before any Bubble Tea program runs) and pin it with `huh.ThemeFunc(func(bool) *huh.Styles { return huh.ThemeCharm(isDark) })`. `.WithTheme(huh.ThemeCharm(isDark))`, as shown in Huh's upgrade guide, does not compile against v2.0.3.

```go check=go/huh-form
form := huh.NewForm(
    huh.NewGroup(
        huh.NewSelect[string]().
            Title("Choose your country").
            Options(huh.NewOptions("USA", "Germany", "Japan")...).
            Value(&country),
        huh.NewInput().
            Title("What's your name?").
            Value(&name).
            Validate(func(s string) error {
                if len(s) == 0 { return errors.New("required") }
                return nil
            }),
        huh.NewConfirm().
            Title("Submit?").
            Value(&confirm),
    ),
)
err := form.Run()
```

Field types: `NewInput`, `NewText` (multi-line), `NewSelect[T]`, `NewMultiSelect[T]`, `NewConfirm`, `NewFilePicker`, `NewNote` (display-only).

**Dynamic forms:** huh's real mechanism is **`Group.WithHideFunc(func() bool)`**, which hides or shows a whole group (a step's worth of fields) from a predicate re-evaluated as form state changes. Per-field hiding is not shipped (open feature requests only), so don't present it as available. To recompute one field from another's value, use `OptionsFunc`/`TitleFunc`/`DescriptionFunc`: a callback plus the fields it depends on, re-run automatically:

```go check=go/huh-options-func
huh.NewSelect[string]().
    OptionsFunc(func() []huh.Option[string] {
        return huh.NewOptions(statesForCountry(country)...)
    }, &country) // recomputed whenever `country` changes
```

**Accessibility:** `form.WithAccessible(true)` bypasses Bubble Tea and asks each field as a plain line-by-line prompt: a numbered list for `Select` (the user types the number), numbers toggled one at a time and `0` to finish for `MultiSelect`, `y`/`n` for `Confirm`, with validation errors printed before the prompt repeats. Huh turns it on by itself only for `TERM=dumb`, so expose your own switch (the README reads `ACCESSIBLE`; gh's `GH_ACCESSIBLE_PROMPTER` drives this mode). Bubble Tea and Bubbles have nothing comparable, so the rest of the app needs its own linear mode; see `visual-patterns.md` → *Accessibility*.

**Full-screen:** `tea.WithAltScreen()` is gone in v2 — declare it on the view instead: `form.WithViewHook(func(v tea.View) tea.View { v.AltScreen = true; return v })`.

**Embedding in Bubble Tea:** `(*huh.Form).Update` returns `(huh.Model, tea.Cmd)`, so assert back: `f, cmd := m.form.Update(msg); if ff, ok := f.(*huh.Form); ok { m.form = ff }`. The parent wraps `Form.View()`'s string in its own `tea.NewView` and checks `m.form.State` (`huh.StateCompleted`/`huh.StateAborted`) to leave the form.

---

## Other Charm libraries worth knowing

- **Glamour** (`charm.land/glamour/v2`) — render Markdown to ANSI. v2 is pure: `WithAutoStyle` and `WithColorProfile` are gone, the default style is `"dark"` (pass `"light"` yourself after detecting the background), and output is downsampled only when printed via `lipgloss.Print`. `gh` renders PR and issue Markdown with it (moved to Glamour v2 in [cli/cli#14148](https://github.com/cli/cli/pull/14148), shipped in v2.103.2).
- **Wish** (`charmbracelet/wish`, v2 at `charm.land/wish/v2`) — serve Bubble Tea apps over SSH. Build each program with `bubbletea.MakeOptions(sess)` (the `bubbletea.Middleware` handler applies it for you) so input, output, and color-profile detection follow the *client's* PTY, not the server's (the v1 `MakeRenderer` helper is gone because Lipgloss v2 no longer owns terminal I/O). `MakeOptions` also installs its own `tea.WithFilter` (ctrl+z suspend becomes resume), and the default `Middleware` appends it after your options, overwriting any filter you set; to keep yours, use `MiddlewareWithProgramHandler` and chain them.
- **gum** — Bubble Tea components for shell scripts (`gum choose|input|confirm|spin`): huh-quality prompts without writing Go. **VHS** records `.tape` scripts to GIFs for documentation.

---

## tview (rivo/tview)

Retained-mode and callback-based, ncurses-style. Built on **tcell v2**. Tags are rare (last v0.42.0, August 2025) and the README installs with `go get github.com/rivo/tview@master`. Powers **k9s** (via derailed's forks).

**Widgets:** `TextView`, `TextArea`, `InputField`, `Table`, `TreeView`, `List`, `Form`, `Image`, `Modal`, `DropDown`, `Button`, `Checkbox`. **Layout:** `Flex` (one-dimensional), `Grid` (two-dimensional), `Pages` (modal/swap views).

```go check=go/tview-hello
app := tview.NewApplication()
list := tview.NewList().
    AddItem("First", "First item", 'a', nil).
    AddItem("Quit", "Quit app", 'q', func() { app.Stop() })
if err := app.SetRoot(list, true).Run(); err != nil {
    panic(err)
}
```

**Threading rule:** any modification to a primitive from a goroutine must go through `app.QueueUpdate(func)` or `app.QueueUpdateDraw(func)`, which run `func` on the main loop. A bare `app.Draw()` from a goroutine is safe (it only schedules a repaint) but does not synchronize your data. The #1 tview pitfall is the opposite direction: calling `Draw()`, `QueueUpdate()`, or `QueueUpdateDraw()` from *inside* an event handler already running on the main goroutine (a key handler, `SetSelectedFunc`) blocks forever, per the tview Concurrency wiki.

**When to choose tview over Bubble Tea:** many widgets must coexist (a "form with 12 fields, table, sidebar"), the team prefers callbacks to message-passing, or you're already on tcell. Bubble Tea suits state-heavy apps but you assemble layout yourself; tview gives more widgets with less code.

---

## gocui (awesome-gocui/gocui)

Minimalist views-as-buffers, each `View` an `io.Writer`: the aesthetic of **lazygit** and **lazydocker**.

**Mental model:** a `Manager` function lays out the views on every redraw (you compute coordinates from `g.Size()`); each view has a name, a position, a buffer you write to, and its own keybindings.

```go check=go/gocui-hello
g, _ := gocui.NewGui(gocui.OutputNormal, true)
defer g.Close()

g.SetManagerFunc(func(g *gocui.Gui) error {
    maxX, maxY := g.Size()
    if v, err := g.SetView("hello", maxX/2-7, maxY/2, maxX/2+7, maxY/2+2, 0); err != nil {
        if !errors.Is(err, gocui.ErrUnknownView) { return err }
        fmt.Fprintln(v, "Hello, World!")
    }
    return nil
})

g.SetKeybinding("", 'q', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
    return gocui.ErrQuit
})

g.MainLoop()
```

**When to choose gocui:** rarely, to maintain an existing app or for its views-as-buffers API. Use `awesome-gocui/gocui` (v1.1.0, 2022; tcell v2). `jesseduffield/gocui` is effectively retired: in April 2026 lazygit copied its fork into `lazygit/pkg/gocui` and moved to tcell v3. For a new lazy-style app (persistent panes, numeric pane keys, single-letter context actions), use Bubble Tea and borrow lazygit's interaction design, not its library.

---

## Lower-level: tcell

`gdamore/tcell` is the long-standing low-level Go terminal library: pure Go, cross-platform, mouse and SGR support. v3 (December 2025) removed terminfo and the termbox compatibility layer and changed the key and cell APIs; tview still uses `tcell/v2`, while lazygit has moved to v3. Use it directly only when building a framework or a custom rendering pipeline; most apps should use Bubble Tea or tview. **Ultraviolet** (`charmbracelet/ultraviolet`), the untagged renderer under Bubble Tea v2, is the same tier; its README warns the API may change.

---

## CLI framing: Cobra and urfave/cli

**Cobra** (`spf13/cobra`) — the dominant subcommand framework for Go. Powers kubectl, gh, hugo, helm, docker. Struct-literal command tree:

```go check=go/cobra-commands
var rootCmd = &cobra.Command{
    Use:   "myapp",
    Short: "A short description",
}

var listCmd = &cobra.Command{
    Use:   "list",
    Short: "List items",
    Run:   func(cmd *cobra.Command, args []string) { /* ... */ },
}

func init() {
    rootCmd.AddCommand(listCmd)
}
```

**Cobra + Bubble Tea integration**: the Cobra `Run` function does `tea.NewProgram(...).Run()`. `PreRun` output is hidden behind the alt screen and reappears at exit; writing to stdout while `Run` is active is what corrupts the frame. Gate the TUI on **stdout** being a terminal (`isatty.IsTerminal(os.Stdout.Fd())`): under `$(myapp)` or `myapp | less` the frame would become data, so print plain output, or draw the UI on stderr with `tea.WithOutput(os.Stderr)` and print only the answer to stdout, as gum does. Piped stdin doesn't stop the TUI (Bubble Tea v2 opens `/dev/tty` for keys); decide separately whether piped input means non-interactive mode.

Since v1.2 Cobra adds a working `completion` subcommand to every root command (hidden when there are no other subcommands). Do not scaffold your own; it would shadow the built-in. Users run `myapp completion bash|zsh|fish|powershell`; customize or disable the default via `rootCmd.CompletionOptions`. `cobra-cli completion ...` completes the generator tool, not your application.

**Fang** (`charm.land/fang/v2`) — an experimental starter kit that wraps Cobra: styled help and error output, automatic `--version`, manpage generation.

**urfave/cli** (`github.com/urfave/cli/v3`; v3 has been the stable line since 2025, v2 is maintenance-only) — alternative subcommand framework with a simpler API. **Kong** (`alecthomas/kong`, struct-tag driven) is a third choice; for one-shot flag parsing the stdlib `flag` package is fine.

**Pretty output without a TUI:** when the user wants pretty CLI output (no full-screen UI), use **lipgloss** standalone with `lipgloss.Println(style.Render(...))`, not `fmt.Println`: in v2 `Render` always emits truecolor, and only `Print*`/`Sprint*`/`Fprint*` downsample and honor `NO_COLOR`, as most Charm CLI tools do. **pterm** bundles color, tables, spinners, progress bars, and prompts; **fatih/color** is plain ANSI color (`color.Red("hello")`).

---

## Testing

**Test in layers, bottom-heavy.** Charm's flagship v2 app (crush) uses zero teatest: it unit-tests handlers with `tea.KeyPressMsg` literals and golden-tests render output via `github.com/charmbracelet/x/exp/golden`. Unit tests on `Update` are the base; the harness is the thin top.

**Layer 1 — `Update` is a pure function.** Construct the model, send a message, assert on state. No harness needed:

```go check=go/update-test
func TestQuitKey(t *testing.T) {
    m := newModel()
    updated, cmd := m.Update(tea.KeyPressMsg{Code: 'q', Text: "q"}) // v2 rune key
    m = updated.(model)
    if cmd == nil { t.Fatal("expected quit cmd") }
}
```

v2 key literals: rune keys are `tea.KeyPressMsg{Code: 'a', Text: "a"}`, specials are `tea.KeyPressMsg{Code: tea.KeyEnter}`, modifiers use `Mod: tea.ModCtrl`. To test a returned Cmd, call it and assert on the message (`tea.QuitMsg` for quit; `tea.BatchMsg` is an exported `[]Cmd` you can unpack and run).

**Layer 2 — teatest** runs the real program against in-memory buffers (no PTY, works in bare CI containers). For Bubble Tea v2 import `github.com/charmbracelet/x/exp/teatest/v2` — teatest did **not** move to charm.land; plain `x/exp/teatest` is the v1 line. Both are pseudo-versioned; teatest/v2 is the official harness.

```go check=go/teatest
tm := teatest.NewTestModel(t, newModel(),
    teatest.WithInitialTermSize(80, 24), // default is 80×24 — pin it anyway
    teatest.WithProgramOptions(tea.WithColorProfile(colorprofile.ASCII)), // v2 only
)
teatest.WaitFor(t, tm.Output(), func(b []byte) bool {
    return bytes.Contains(b, []byte("ready"))
}, teatest.WithDuration(5*time.Second)) // defaults (1s timeout, 50ms poll) are tight for CI
tm.Type("hello")                        // v2: emits one KeyPressMsg per rune
tm.Send(tea.KeyPressMsg{Code: tea.KeyEnter})
tm.WaitFinished(t, teatest.WithFinalTimeout(2*time.Second))
out, _ := io.ReadAll(tm.FinalOutput(t))
teatest.RequireEqualOutput(t, out) // golden file: testdata/<TestName>.golden
```

Always pass `WithFinalTimeout` — `FinalModel`/`FinalOutput`/`WaitFinished` block forever without it. Goldens hold raw bytes, escape sequences included. Refresh with `go test ./... -update` and add `*.golden -text` to `.gitattributes` so git never rewrites them.

**Test at the contract sizes:** golden-test 80×24, 60 columns, and your declared minimum (one golden per size, e.g. `TestView/60x24`), and send `tea.WindowSizeMsg{Width: 60, Height: 24}` to `Update` (or `tm.Send(...)` mid-run) to assert the layout reflows rather than keeping the startup width. **Determinism in CI:** the #1 golden-file flake is color-profile detection: v2 wraps output in a `colorprofile.Writer`, so escapes vary with `TERM`/`COLORTERM`/`NO_COLOR`. Pin the profile (`tea.WithColorProfile(colorprofile.ASCII)`, v2-only; on v1 `lipgloss.SetColorProfile(termenv.Ascii)`) and the term size, or goldens will flap.

**E2E:** teatest deliberately avoids PTYs and Go PTY/expect practice is thin. For real-terminal visual regression, use VHS golden output (`Output golden.ascii` in a tape), which needs `ttyd` and `ffmpeg` (`charmbracelet/vhs-action` for CI).

---

## Debugging

**stdout is off-limits while the program runs**: Bubble Tea holds the terminal in raw mode, so `fmt.Println` output is swallowed or corrupts the frame. Log to a file instead (unchanged in v2):

```go check=go/log-to-file
if len(os.Getenv("DEBUG")) > 0 {
    f, err := tea.LogToFile("debug.log", "debug")
    if err != nil {
        fmt.Fprintln(os.Stderr, "fatal:", err) // otherwise logs land in the TUI
        os.Exit(1)
    }
    defer f.Close()
}
```

Run `DEBUG=1 go run .` in one terminal and `tail -f debug.log` in another; `log.Println` anywhere lands in the file, and `tea.LogToFileWith` takes a custom logger. **Breakpoints:** the TUI and delve fight over stdin/stdout, so run delve headless (`dlv debug --headless --api-version=2 --listen=127.0.0.1:43000 .`) and `dlv connect 127.0.0.1:43000` from a second terminal.

**Profiling a sluggish TUI:** serve `net/http/pprof` on a loopback port rather than file-based `pprof.StartCPUProfile`: a background goroutine on `localhost:6060` never touches stdin/stdout, so it can't collide with raw-mode rendering, and there is no SIGINT/flush ceremony. Gate it behind an env var:

```go check=go/pprof
import (
    "net/http"
    _ "net/http/pprof"
)
if os.Getenv("MYAPP_PROFILE") != "" {
    go func() { http.ListenAndServe("localhost:6060", nil) }()
}
```

Then `go tool pprof -http=:8080 http://localhost:6060/debug/pprof/profile` from a second terminal. The usual cost sink is uncached work in `View()` (recomputed `lipgloss.Width()` calls, string rebuilds).

---

## Cross-platform notes

Bubble Tea, tview, and gocui all work on Linux, macOS, and Windows. Target Windows Terminal (Windows 10+; older `cmd.exe` lacks some ANSI) and test mouse events there if Windows is supported. Signals, `WT_SESSION`, Unicode output, multiplexer keys: `terminal-protocols.md` → *Terminal environments*.

---
