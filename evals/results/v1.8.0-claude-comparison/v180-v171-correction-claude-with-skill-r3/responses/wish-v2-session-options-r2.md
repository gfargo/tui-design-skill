No. `MakeRenderer` was a Wish v1 helper, and it's gone in Wish v2. In v1, Lipgloss handled terminal output, so each session needed its own `lipgloss.Renderer` to get the right color profile. Lipgloss v2 never touches the terminal. Bubble Tea v2 handles output and reduces colors to fit the terminal as it writes. So all you have to do is point each `tea.Program` at the session.

## Use the Wish bubbletea middleware (or `MakeOptions`)

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/wish/v2"
    "charm.land/wish/v2/bubbletea"
    "github.com/charmbracelet/ssh"
)

srv, err := wish.NewServer(
    wish.WithAddress(":23234"),
    wish.WithHostKeyPath(".ssh/id_ed25519"),
    wish.WithMiddleware(
        bubbletea.Middleware(func(sess ssh.Session) (tea.Model, []tea.ProgramOption) {
            return newModel(), nil // the middleware wires I/O + color profile to this session
        }),
    ),
)
```

`bubbletea.Middleware` calls `bubbletea.MakeOptions(sess)` for you. That function sets the program's input, output and color-profile detection from the client's PTY and environment (`TERM`, `COLORTERM`), not from the server process. If you build the `tea.Program` yourself, pass `bubbletea.MakeOptions(sess)...` to `tea.NewProgram`.

**Watch out for filters:** `MakeOptions` installs its own `tea.WithFilter`, which turns ctrl+z into resume, since suspending doesn't work over SSH. The default `Middleware` adds its options after yours, so any filter you pass gets overwritten. If you need your own filter, use `bubbletea.MiddlewareWithProgramHandler`, build the program yourself, and call the Wish filter from inside yours.

## Don't do these on the server side

- **Don't create styles once at startup based on detection.** You can define styles globally with full-color values. They're reduced to each session's profile as Bubble Tea writes them out.
- **Don't call `lipgloss.HasDarkBackground(os.Stdin, os.Stdout)`.** On the server, that checks the server's terminal (or none at all). Even with the session's I/O, it would compete with Bubble Tea for input.
- **Don't force a profile with `tea.WithColorProfile`** unless you mean to, for example ASCII for golden tests. It overrides the client detection.

## Light/dark background is per session too

The color profile is detected automatically, but the background color isn't. Ask each client's terminal from inside the program:

```go
func (m model) Init() tea.Cmd { return tea.RequestBackgroundColor }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.BackgroundColorMsg:
        m.styles = newStyles(lipgloss.LightDark(msg.IsDark()))
    }
    return m, nil
}
```

Keep these styles on the model, not in globals, because each session gets its own model. Draw with a default palette first and treat the reply as an upgrade. Some SSH clients and terminals never answer the background-color query (OSC 11).

To check it, connect from a truecolor terminal and from a client with `TERM=xterm-256color` or `NO_COLOR=1`, for example `TERM=xterm-256color ssh -p 23234 localhost`. Each session should render at its own color depth.
