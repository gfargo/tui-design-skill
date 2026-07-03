# Go ecosystem — Bubble Tea, tview, gocui, Cobra

The Go TUI landscape consolidated around two camps: the **Charm stack** (Bubble Tea + Lipgloss + Bubbles + Huh) for new projects, and **tcell + tview** for traditional widget-rich apps. **gocui** is a third lineage powering lazygit/lazydocker. CLI framing comes from **Cobra** (kubectl, gh, hugo, helm, docker) or `urfave/cli`.

## Quick recommendation

| If the user wants… | Use |
|---|---|
| Modern TUI with clean architecture and Charm aesthetic | **Bubble Tea + Lipgloss + Bubbles** |
| Multi-pane vim-keybinding "lazy*"-style app | **gocui** (`awesome-gocui/gocui` or `jesseduffield/gocui`) |
| Heavy data exploration with tables, trees, forms | **tview** (callback-style, retained-mode) |
| One-shot fancy CLI prompts only | **Huh** (Go form library) or **gum** (shell wrapper) |
| Markdown rendering in terminal | **Glamour** |
| Pretty CLI output, no full-screen | **pterm** |
| Subcommand framing for any of the above | **Cobra** or **urfave/cli** |
| TUI served over SSH | **Wish** (wraps Bubble Tea apps as SSH server) |

**Default choice for new projects: Bubble Tea + Lipgloss + Bubbles + Cobra.** This is what `charm.land` apps, `gh`, and most new Go TUIs use.

---

## Bubble Tea (charmbracelet/bubbletea)

The Elm Architecture in Go, and the most widely used Go TUI framework. Pure functional reactive — `Model → Update(Msg) → (Model, Cmd) → View() tea.View`.

**v2 is stable** (v2.0.0 shipped February 2026 after betas/RCs through 2025; current is v2.0.x). What changed and why it matters:
- **New "Cursed Renderer"** — rewritten from scratch on the ncurses diffing algorithm; faster and more accurate redraws. Bubble Tea now owns terminal I/O and Lipgloss became pure (no more I/O fights between the two).
- **Progressive keyboard enhancements** — with the Kitty protocol you can finally bind `shift+enter`, `ctrl+i` distinct from `tab`, `super+space`, etc. Always keep a legacy fallback.
- **Import path moved** to `charm.land/bubbletea/v2` (vanity domain over `github.com/charmbracelet/bubbletea/v2`). All Charm v2 libraries import from `charm.land/<name>/v2` — bubbletea, bubbles, lipgloss, huh, wish — keep them on the same major.

**Migrating v1 → v2:** the MVU shape survives, but every model gets touched: `View()` now returns `tea.View` instead of `string`, key handling moves to `tea.KeyPressMsg`, and the alt-screen/mouse program options moved onto the view. If you're on v1 and it works, there's no urgency; if you're starting fresh, start on v2.

**The mental model:**
- **Model**: a single struct holding all state.
- **Init**: returns the initial Cmd (or `nil`).
- **Update(msg)**: pure function returning `(newModel, Cmd)`. The only place state changes.
- **View()**: pure function returning the entire frame as a `tea.View` — content plus frame-level declarations (alt screen, mouse mode, cursor). Bubble Tea diffs against the previous frame and emits minimal ANSI.
- **Cmds and Msgs**: side effects live in `tea.Cmd` (a `func() tea.Msg`); messages flow back through Update.

**Canonical structure:**

```go
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

**Frame-level declarations live on the view, not the program.** `tea.WithAltScreen()`, `tea.WithMouseCellMotion()`, and `tea.WithMouseAllMotion()` were removed in v2 — set `v.AltScreen = true` and `v.MouseMode = tea.MouseModeCellMotion` (or `tea.MouseModeAllMotion` for hover) in `View()`.

**Important options:**
- `tea.WithInput(reader)` / `tea.WithOutput(writer)` — useful for testing or Wish.
- `tea.WithColorProfile(p)` — force a specific color profile; the testing hook for golden-file output.

**Async via Cmds:**
```go
func fetchData() tea.Msg {
    data, err := http.Get(...)
    if err != nil { return errMsg{err} }
    return dataMsg{data}
}

// In Update, when you want to fetch:
return m, fetchData
```

`tea.Cmd` is `func() tea.Msg`. The runtime calls them in goroutines and routes the returned `Msg` back through `Update`. **Never block in `Update`** — anything I/O goes in a Cmd.

**`tea.Batch(cmds...)`** for parallel commands; **`tea.Sequence(cmds...)`** for ordered.

**Pitfalls:**
- `len(string)` ≠ display width. Use `lipgloss.Width()`.
- Goroutines never call `View()` directly — send via `program.Send(msg)`.
- CJK/emoji width in the v2 stack goes through `charmbracelet/x/ansi` (uniseg-based grapheme clustering) — trust `lipgloss.Width()`, never `len()`.
- Don't `fmt.Println` — corrupts the screen. Use `tea.LogToFile("debug.log", "DEBUG")` (see **Debugging** below).
- Cobra + Bubble Tea: don't write to stdout from `PreRun` (alt-screen eats it).

---

## Lipgloss (charmbracelet/lipgloss)

CSS-in-Go declarative styling — immutable `Style` values rendered to ANSI strings. The companion to Bubble Tea, but usable standalone.

**Canonical use:**

```go
var titleStyle = lipgloss.NewStyle().
    Bold(true).
    Foreground(lipgloss.Color("#FAFAFA")).
    Background(lipgloss.Color("#7D56F4")).
    Padding(0, 1).
    BorderStyle(lipgloss.RoundedBorder()).
    BorderForeground(lipgloss.Color("63"))

fmt.Println(titleStyle.Render("Hello, world"))
```

**Layout helpers:**
- `lipgloss.JoinHorizontal(lipgloss.Top, left, right)` — side-by-side.
- `lipgloss.JoinVertical(lipgloss.Left, top, middle, bottom)` — stacked.
- `lipgloss.Place(width, height, hPos, vPos, content)` — center/anchor in a box.
- `lipgloss.Width(s)` / `lipgloss.Height(s)` — measure rendered output (handles ANSI and runewidth correctly).

**No flexbox.** You compute widths from the cached `tea.WindowSizeMsg`:

```go
case tea.WindowSizeMsg:
    m.width, m.height = msg.Width, msg.Height
    m.leftPaneWidth = msg.Width / 3
    m.rightPaneWidth = msg.Width - m.leftPaneWidth
```

**Light/dark theming:** Lipgloss v2 is pure — it never touches the terminal, so *your app* queries the background once and picks variants:
```go
hasDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)
lightDark := lipgloss.LightDark(hasDark)
fg := lightDark(lipgloss.Color("#236"), lipgloss.Color("#cef"))
```
The old `AdaptiveColor` survives only in `charm.land/lipgloss/v2/compat` for migrations; prefer `LightDark` in new code.

**Sub-packages:**
- `lipgloss/table` — bordered, styled tables with column alignment.
- `lipgloss/list` — bullet/numbered/tree lists with custom enumerators.
- `lipgloss/tree` — hierarchical trees with custom indenters.

**Testing tip:** `SetColorProfile` is gone in v2. Downsampling now happens at write time — `lipgloss.Print`/`Println`/`Sprint` detect the output's profile via the `colorprofile` package. In Bubble Tea programs, force ASCII for CI/golden-file tests with `tea.WithColorProfile(colorprofile.Ascii)`.

---

## Bubbles (charmbracelet/bubbles)

The component library for Bubble Tea. Each Bubble is itself a `tea.Model` you embed and forward messages to.

**Components shipped:**
- **`textinput`** — single-line input with placeholder, suggestions, validation.
- **`textarea`** — multi-line input with line numbers.
- **`list`** — virtualized list with filtering, pagination, custom delegate for row rendering.
- **`table`** — virtualized table with selection, sorting.
- **`viewport`** — scrollable region for long content.
- **`spinner`** — Braille/Meter/MiniDot/Dot/Line/Pulse/Points/Globe/Moon spinner styles.
- **`progress`** — gradient-filled progress bar with percent.
- **`paginator`** — page indicators.
- **`filepicker`** — file system browser.
- **`help`** — auto-rendered footer hint bar from a `key.KeyMap`.
- **`key`** — declarative key bindings.
- **`cursor`**, **`stopwatch`**, **`timer`** — utilities.

**Embedding pattern:**

```go
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

func (m model) View() string {
    return m.list.View() + "\n" + m.help.View(m.keys)
}
```

**Declarative keys with `key.Binding`:**

```go
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

// In Update:
case tea.KeyMsg:
    switch {
    case key.Matches(msg, keys.Quit):
        return m, tea.Quit
    case key.Matches(msg, keys.Up):
        // ...
    }
```

The `help` Bubble auto-renders the footer from these bindings — define once, get the hint bar for free.

---

## Huh (charmbracelet/huh)

Forms library on top of Bubble Tea. Best for one-shot interactive prompts (multi-step wizards) and embeddable form panes inside larger TUIs. Huh v2 (`charm.land/huh/v2`, released March 2026) is built on Bubble Tea v2 — themes now take an `isDark` bool (e.g. `huh.ThemeCharm(isDark)`) instead of self-detecting.

```go
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

**Accessibility:** `form.WithAccessible(true)` switches to plain prompts (line-by-line, no alt-screen) for screen readers and limited terminals — a genuinely thoughtful feature.

**Full-screen:** `tea.WithAltScreen()` is gone in v2 — declare it on the view instead: `form.WithViewHook(func(v tea.View) tea.View { v.AltScreen = true; return v })`.

**Embedding in Bubble Tea:** forward messages via `m.form, cmd = m.form.Update(msg)`.

---

## Other Charm libraries worth knowing

- **Glamour** (`charmbracelet/glamour`) — render Markdown to ANSI. Themable via JSON stylesheets. Used for `gh` PR/issue rendering, `glow` markdown viewer.
- **Wish** (`charmbracelet/wish`, v2 at `charm.land/wish/v2`) — serve Bubble Tea apps over SSH with HTTP-style middleware. Per-session Lipgloss renderers (`bm.MakeRenderer(sess)`) use the *client's* color profile, not the server's.
- **Soft Serve** — git server with a Bubble Tea TUI; built on Wish.
- **gum** — shell-script wrapper around Bubble Tea components. `gum choose`, `gum input`, `gum confirm`, `gum spin`. Use when scripting Bash and you want huh-quality prompts without writing Go.
- **VHS** — record terminal sessions to GIFs from a `.tape` script. Gold for documentation.

---

## tview (rivo/tview)

Retained-mode, callback-based — the traditional ncurses style. Built on **tcell** (gdamore's terminal library, replacement for termbox). Mature and maintained slowly but steadily. Powers **k9s**.

**Widgets:** `Box`, `TextView`, `TextArea`, `InputField`, `Table`, `TreeView`, `List`, `Form`, `Image`, `Modal`, `Pages`, `Flex`, `Grid`, `Frame`, `DropDown`, `Button`, `Checkbox`.

**Layout:** `Flex` (one-dimensional), `Grid` (two-dimensional), `Pages` (modal/swap views).

**Hello world:**

```go
app := tview.NewApplication()
list := tview.NewList().
    AddItem("First", "First item", 'a', nil).
    AddItem("Quit", "Quit app", 'q', func() { app.Stop() })
if err := app.SetRoot(list, true).Run(); err != nil {
    panic(err)
}
```

**Threading rule:** `app.QueueUpdateDraw(func)` is **required** for any modification from a goroutine. Calling `app.Draw()` from a non-main goroutine causes deadlocks. This is the #1 tview pitfall.

**When to choose tview over Bubble Tea:** you have many widgets that need to coexist (a real "form with 12 fields, table, sidebar"), the team prefers callbacks over message-passing, or you're already on tcell. Bubble Tea is more ergonomic for state-heavy apps but you assemble layout manually; tview gives you a richer widget set with less code.

---

## gocui (awesome-gocui/gocui)

Minimalist views-as-buffers — each `View` implements `io.Writer`. The aesthetic of **lazygit** and **lazydocker**.

**Mental model:**
- Define a `Manager` function that's called on every redraw to lay out views.
- Each view has a name, position, and a buffer you write to.
- Per-view keybindings.
- Manual layout (you compute coordinates from `g.Size()`).

**Hello world:**

```go
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

**When to choose gocui:** you specifically want the lazygit aesthetic — multiple persistent panes, vim-style numeric keys to switch panes, single-letter context-sensitive actions. The `jesseduffield/gocui` fork (used by lazygit) has more features than the upstream `awesome-gocui` fork. For a brand-new app, lean Bubble Tea unless you really want this exact paradigm.

---

## Lower-level: tcell

`gdamore/tcell` is the modern alternative to termbox-go: terminfo-based, cross-platform, mouse and SGR support, used by tview internally. Use directly only if you're building a framework or have very specific needs (custom rendering pipeline, embedded use). Most apps should use Bubble Tea or tview on top.

**Ultraviolet** (`charmbracelet/ultraviolet`) is the standalone rendering engine underneath Bubble Tea v2's renderer — the same tier as tcell if you're building your own framework.

---

## CLI framing: Cobra and urfave/cli

**Cobra** (`spf13/cobra`) — the dominant subcommand framework for Go. Powers kubectl, gh, hugo, helm, docker. Struct-literal command tree:

```go
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

**Cobra + Bubble Tea integration**: the Cobra `Run` function does `tea.NewProgram(...).Run()`. Don't write to stdout from `PreRun` if you'll enter alt-screen (output gets eaten). For commands that take pipe input, check `isatty.IsTerminal(os.Stdin.Fd())` before launching the TUI; if piped, run in non-interactive mode.

Cobra ships shell completion generation (`cobra-cli completion bash|zsh|fish|powershell`) — wire it up; users expect it.

**Fang** (`charmbracelet/fang`) — the CLI starter kit that wraps Cobra: styled help and error output, automatic `--version`, manpage generation. The idiomatic Cobra companion in a Charm-stack app.

**urfave/cli** (`urfave/cli/v2`) — alternative subcommand framework, simpler API, less popular but used by syncthing and others.

For one-shot `flag` parsing only, the stdlib `flag` package is fine.

---

## Output formatting (non-TUI)

When the user wants pretty CLI output (no full-screen UI):

- **lipgloss** — yes, you can use it standalone for `fmt.Println(style.Render(...))`. This is what most Charm CLI tools do.
- **pterm** — color, tables, spinners, progress bars, charts, prompts. All-in-one. Less elegant API than Lipgloss but has more built-in.
- **fatih/color** — simple ANSI color wrapper. Used by countless tools. `color.Red("hello")`, `color.New(color.FgYellow, color.Bold).Println(...)`.

---

## Testing

**Test in layers, bottom-heavy.** Even Charm's flagship v2 app (crush, 163 test files) uses zero teatest — it unit-tests handlers with `tea.KeyPressMsg` literals and golden-tests render output via `github.com/charmbracelet/x/exp/golden`. Unit tests on `Update` are the base of the pyramid; the harness is the thin top.

**Layer 1 — `Update` is a pure function.** Construct the model, send a message, assert on state. No harness needed:

```go
func TestQuitKey(t *testing.T) {
    m := newModel()
    updated, cmd := m.Update(tea.KeyPressMsg{Code: 'q', Text: "q"}) // v2 rune key
    m = updated.(model)
    if cmd == nil { t.Fatal("expected quit cmd") }
}
```

v2 key literals: rune keys are `tea.KeyPressMsg{Code: 'a', Text: "a"}`, specials are `tea.KeyPressMsg{Code: tea.KeyEnter}`, modifiers use `Mod: tea.ModCtrl`. To test a returned Cmd, just call it — `tea.Cmd` is `func() Msg` — and assert on the message (`tea.QuitMsg` for quit; `tea.BatchMsg` is an exported `[]Cmd` you can unpack and run).

**Layer 2 — teatest** runs the real program against in-memory buffers (no PTY, works in bare CI containers). For Bubble Tea v2 import `github.com/charmbracelet/x/exp/teatest/v2` — teatest did **not** move to charm.land; plain `x/exp/teatest` is the v1 line. Both are pseudo-versioned experiments, but teatest/v2 is what maintainers point to as the official harness.

```go
tm := teatest.NewTestModel(t, newModel(),
    teatest.WithInitialTermSize(80, 24), // default is 80×24 — pin it anyway
    teatest.WithProgramOptions(tea.WithColorProfile(colorprofile.Ascii)), // v2 only
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

Always pass `WithFinalTimeout` — `FinalModel`/`FinalOutput`/`WaitFinished` block forever without it. Goldens are stored escaped (diffable text) and refreshed with `go test ./... -update`.

**Determinism in CI:** the #1 golden-file flake is color-profile detection — v2 wraps output in a `colorprofile.Writer`, and the emitted escapes vary with `TERM`/`COLORTERM`/`NO_COLOR`. Pin the profile (`tea.WithColorProfile(colorprofile.Ascii)` — v2-only; on v1 use `lipgloss.SetColorProfile(termenv.Ascii)`) and the term size, or goldens will flap. Bubble Tea's own teatest example is currently skipped over exactly this.

**E2E:** PTY/expect practice is thin in Go — teatest deliberately avoids PTYs. For real-terminal visual regression, VHS golden output (`Output golden.ascii` in a tape) is the blessed heavyweight option; needs `ttyd` + `ffmpeg`, with `charmbracelet/vhs-action` for CI.

---

## Debugging

**stdout is off-limits while the program runs** — Bubble Tea holds the terminal in raw mode on the alternate screen, so `fmt.Println` output gets swallowed or corrupts the frame. Log to a file instead (unchanged in v2):

```go
if len(os.Getenv("DEBUG")) > 0 {
    f, _ := tea.LogToFile("debug.log", "debug")
    defer f.Close()
}
```

Run `DEBUG=1 go run .` in one terminal and `tail -f debug.log` in another — the documented convention. `log.Println` from anywhere in Update or Cmds lands in the file; v2 adds `tea.LogToFileWith` for a custom logger.

**Breakpoints:** the TUI and delve fight over stdin/stdout, so run delve headless — `dlv debug --headless --api-version=2 --listen=127.0.0.1:43000 .`, then `dlv connect 127.0.0.1:43000` from a second terminal.

---

## Notable Go TUI apps to study

- **lazygit** (gocui) — multi-pane git TUI; the canonical "lazy*" aesthetic.
- **lazydocker** (gocui) — same paradigm for Docker.
- **k9s** (tview) — Kubernetes TUI; command-mode navigation, drill-down stack.
- **gh** (Cobra + Lipgloss) — GitHub CLI; not a full TUI, but excellent CLI design.
- **Crush** (Bubble Tea v2) — Charm's AI coding agent; the flagship production v2 app.
- **glow** (Bubble Tea) — markdown reader.
- **soft serve** (Wish + Bubble Tea) — SSH-served git UI.
- **circumflex** — Hacker News reader (Bubble Tea).
- **gh dash** (Bubble Tea) — GitHub dashboard.
- **superfile** (Bubble Tea) — file manager.
- **wishlist** (Wish) — SSH directory.

When the user is building something similar to one of these, point them at it as a reference. The repos are open and idiomatic.

---

## Cross-platform notes

Bubble Tea, tview, and gocui all work on Linux, macOS, and Windows (Terminal, conhost, ConEmu). Windows quirks:
- Older `cmd.exe` doesn't support all ANSI; target Windows Terminal (Windows 10+).
- `Ctrl+Z` (SIGTSTP) doesn't exist on Windows; that's fine, just don't rely on suspend behavior universally.
- Mouse events differ slightly; libraries abstract this but test on Windows if it's a target.

For SSH-served TUIs, **Wish** is the right answer — it handles per-session terminal capabilities (the client's truecolor support, not the server's) and gives you middleware for auth, logging, rate limiting.

---

## Idioms summary

- **Bubble Tea**: All I/O in `tea.Cmd`s. Cache `WindowSizeMsg` for layout. Forward messages to child Bubbles. Use `tea.Batch` for parallel, `tea.Sequence` for ordered. Use `key.Binding` + `key.Matches` for declarative keys. Use `tea.LogToFile` for debug — never `fmt.Println`.
- **Lipgloss**: Define styles once at package level (they're immutable). Use `JoinHorizontal`/`JoinVertical`/`Place` for layout. Use `LightDark` for theme support. Use `Width()`/`Height()` to measure, not `len()`.
- **Bubbles**: Embed components in your model. Forward `Update` calls. Use `key.KeyMap` + `help.Model` for the footer hint bar.
- **tview**: Use `app.QueueUpdateDraw` for goroutine-originated changes — never `app.Draw` directly off-thread.
- **gocui**: Layout is your `Manager` function. Each view is an `io.Writer`. Use `gocui.ErrQuit` to exit.
- **Cobra**: Wire up shell completions. Don't print to stdout in `PreRun` if entering alt-screen.

For deeper patterns shared across Go apps, see `references/visual-patterns.md` and `references/interaction-patterns.md`.
