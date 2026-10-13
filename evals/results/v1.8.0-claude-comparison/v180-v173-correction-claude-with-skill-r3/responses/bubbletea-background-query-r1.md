The stutter comes from `HasDarkBackground` itself. It writes an OSC 11 query to the terminal and then reads stdin until the reply arrives. Bubble Tea is already reading stdin, so the two readers fight over your keypresses. Calling it inside `Update` makes it worse: `Update` runs on the event loop, so the program freezes while the query waits, and it does this on every call.

**Fix: ask Bubble Tea to run the query and handle the reply as a message.**

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/lipgloss/v2"
)

type styles struct {
    title lipgloss.Style
    muted lipgloss.Style
}

func newStyles(isDark bool) styles {
    ld := lipgloss.LightDark(isDark)
    return styles{
        title: lipgloss.NewStyle().Bold(true).Foreground(ld(lipgloss.Color("#236"), lipgloss.Color("#cef"))),
        muted: lipgloss.NewStyle().Foreground(ld(lipgloss.Color("#666"), lipgloss.Color("#999"))),
    }
}

type model struct {
    styles styles
    // ...
}

func initialModel() model {
    // Start with a default palette so the first frame looks right without a reply.
    return model{styles: newStyles(true)}
}

func (m model) Init() tea.Cmd {
    return tea.RequestBackgroundColor // query once; Bubble Tea handles the I/O
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.BackgroundColorMsg:
        m.styles = newStyles(msg.IsDark()) // rebuild once, then just use m.styles
    // ... key handling etc.
    }
    return m, nil
}
```

**Why this works and what to watch for:**
- **Query once, store the result.** Build your styles when the reply arrives and keep them on the model. Don't look up the theme again in `Update` or `View`.
- **The reply is a bonus, not a requirement.** It may never arrive. Some terminals don't answer OSC 11, and since v2.0.10, `tea.WithInput(nil)` skips all terminal queries. So always start with a usable default palette, as shown above.
- **Use `HasDarkBackground` only before the program starts.** It's fine in a plain CLI, or in `main` before `tea.NewProgram(...).Run()`. Never call it while Bubble Tea is running.
- **Prefer `lipgloss.LightDark` over `AdaptiveColor`.** `AdaptiveColor` now only lives in `lipgloss/v2/compat` to help with migrations.

More generally, `Update` should never block. Any terminal or other I/O belongs in a `tea.Cmd`, whose result comes back to `Update` as a message.
