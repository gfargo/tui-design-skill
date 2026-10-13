The stutter comes from `HasDarkBackground` itself. It writes an OSC 11 query to the terminal and then reads the reply from stdin. Bubble Tea is already reading stdin, so the two readers compete. Keystrokes can get swallowed or delayed, and the call can block `Update` until it times out. Calling it from `Update` repeats that on every message.

**Fix: ask Bubble Tea for the color once and handle the reply as a message.**

```go
type model struct {
	styles styles // your themed styles
	// ...
}

func newModel() model {
	// Render with a sensible default right away; the reply may never come.
	return model{styles: newStyles(true)}
}

func (m model) Init() tea.Cmd {
	return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.BackgroundColorMsg:
		m.styles = newStyles(msg.IsDark()) // rebuild once, then cache
		return m, nil
	// ... key handling etc.
	}
	return m, nil
}

func newStyles(isDark bool) styles {
	lightDark := lipgloss.LightDark(isDark)
	return styles{
		title: lipgloss.NewStyle().
			Foreground(lightDark(lipgloss.Color("#236"), lipgloss.Color("#cef"))),
		// ...
	}
}
```

**Why this fixes it:**
- Bubble Tea sends the query and parses the reply in its own input loop, so nothing else reads stdin.
- The theme is worked out once and stored on the model. `Update` and `View` only read the cached styles.

**Things to watch for:**
- **The reply might never arrive.** Some terminals don't answer OSC 11. Also, since v2.0.10, `tea.WithInput(nil)` skips all terminal queries. Always render a default palette first and treat the reply as an upgrade.
- **Keep `HasDarkBackground` for code that runs without Bubble Tea.** That includes `main` before `tea.NewProgram(...).Run()` and plain CLI output. Lip Gloss v2 never touches the terminal by itself, so calling it there is fine.
- **Replace `AdaptiveColor` with `lipgloss.LightDark(isDark)`.** `AdaptiveColor` now exists only in `lipgloss/v2/compat`, for migrations.

This follows the skill's Go ecosystem reference, `references/ecosystem-go.md:170-177`.
