No. Don't call `bubbletea.MakeRenderer(sess)`. That was the Wish v1 / Lip Gloss v1 approach. Lip Gloss v2 removed the `*lipgloss.Renderer` type, so Wish v2 has no per-session renderer to create.

## How it works in v2

- **Lip Gloss v2 styles are plain values.** They hold whatever colors you give them and know nothing about the terminal. You can define them once and share them across sessions.
- **Bubble Tea v2 handles color at output time.** Each `tea.Program` detects a color profile from its own output and environment. When it writes a frame, it downsamples the colors to fit (TrueColor → ANSI256 → ANSI → plain text).
- **The Wish v2 `bubbletea` middleware builds each program from the SSH session.** It uses the session for input and output, and passes the session's environment, including the PTY's `TERM`. So color detection runs per client, not against the server's terminal.

You get per-client color handling just by using the middleware:

```go
srv, err := wish.NewServer(
    wish.WithAddress(":23234"),
    wish.WithHostKeyPath(".ssh/id_ed25519"),
    wish.WithMiddleware(
        bubbletea.Middleware(teaHandler),
        activeterm.Middleware(), // require a PTY
        logging.Middleware(),
    ),
)

func teaHandler(s ssh.Session) (tea.Model, []tea.ProgramOption) {
    return newModel(), nil // no renderer plumbing needed
}
```

## Light/dark backgrounds per client

Color depth is handled for you, but choosing light or dark colors is up to the model. Ask the client's terminal for its background color:

```go
type model struct {
    styles styles
}

func (m model) Init() tea.Cmd {
    return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.BackgroundColorMsg:
        m.styles = newStyles(msg.IsDark())
    case tea.ColorProfileMsg:
        // Optional: msg.Profile is this client's detected profile,
        // if you want to change more than colors (e.g. glyphs).
    }
    return m, nil
}

func newStyles(isDark bool) styles {
    lightDark := lipgloss.LightDark(isDark)
    return styles{
        title: lipgloss.NewStyle().
            Foreground(lightDark(lipgloss.Color("#5A56E0"), lipgloss.Color("#B8B5FF"))),
    }
}
```

## Things to avoid in a Wish server

These all inspect the **server's** stdin, stdout or environment, so they give the wrong answer for remote clients:

- `lipgloss.HasDarkBackground(os.Stdin, os.Stdout)`
- `colorprofile.Detect(os.Stdout, os.Environ())`
- `lipgloss.Println` / `lipgloss.Sprint` and similar standalone printing helpers. They downsample for the local stdout. Inside a program, return strings from `View()` and let Bubble Tea do the downsampling.
- Package-level `init()` code that picks light or dark colors once for every session.

If you need to override detection for a session, for example based on a flag the user passes, return `tea.WithColorProfile(colorprofile.ANSI256)` (or another profile) in the handler's `[]tea.ProgramOption`.

I wrote this from memory of the v2 APIs; there's no Go code in your working directory to check against. If something doesn't compile, check the names against your module versions. `tea.ColorProfileMsg`, `tea.WithColorProfile` and the handler signature are the most likely to differ.
