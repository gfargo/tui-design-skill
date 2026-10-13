The stutter happens because `lipgloss.HasDarkBackground` sends an OSC 11 query to the terminal and then **blocks while it reads the reply from stdin**. Bubble Tea is already reading stdin for key and mouse events, so the two readers compete. The terminal's reply can get split between them, and `Update` freezes while it waits, which stalls the whole event loop. More generally, `Update` should never do blocking I/O.

That helper is meant for standalone Lip Gloss use, outside a Bubble Tea program. Inside Bubble Tea v2, ask the runtime to make the query and handle the reply as a message:

```go
type model struct {
	isDark bool
	styles styles
}

func (m model) Init() tea.Cmd {
	// Ask the terminal for its background color; the reply arrives as a message.
	return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.BackgroundColorMsg:
		m.isDark = msg.IsDark()
		m.styles = newStyles(m.isDark) // rebuild styles once, not on every render
		return m, nil
	// ... key handling etc.
	}
	return m, nil
}

type styles struct {
	title lipgloss.Style
}

func newStyles(isDark bool) styles {
	lightDark := lipgloss.LightDark(isDark)
	return styles{
		title: lipgloss.NewStyle().
			Foreground(lightDark(lipgloss.Color("#1a1a1a"), lipgloss.Color("#f0f0f0"))),
	}
}
```

**Tips:**
- **Start with a default theme.** Build styles in your constructor (for example `newStyles(true)`) so the first frame renders before the reply arrives. Some terminals (and tmux/screen setups) never answer the query, so the app must work without it.
- **Build styles once.** Recreate them only when `BackgroundColorMsg` arrives, not on every `View` call.
- **Re-query if needed.** If you want to catch the user switching their terminal theme mid-session, return `tea.RequestBackgroundColor` again from `Update`, for example on focus regained. It's non-blocking, so this is safe.
