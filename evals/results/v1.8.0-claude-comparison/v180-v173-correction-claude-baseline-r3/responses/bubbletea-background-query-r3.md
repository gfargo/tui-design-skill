The stutter comes from `lipgloss.HasDarkBackground`. It's a blocking terminal query: it writes an OSC 11 escape sequence and then reads stdin until the terminal replies or the call times out. Inside `Update`, that causes two problems:

1. **It blocks the event loop.** No messages are handled while it waits, so a slow terminal, an SSH link, or one that never replies stalls your UI for the whole timeout.
2. **It competes with Bubble Tea for stdin.** Bubble Tea's input reader is already reading stdin. The two can steal each other's bytes, so keystrokes get dropped or the reply gets parsed as junk input.

And because `Update` runs on every message, you're doing this over and over.

## Ask Bubble Tea instead

Bubble Tea v2 can make this query through its own input pipeline and send you the answer as a message:

```go
type model struct {
	isDark bool
	styles styles
}

func (m model) Init() tea.Cmd {
	return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.BackgroundColorMsg:
		m.isDark = msg.IsDark()
		m.styles = newStyles(m.isDark) // build once, not in View
		return m, nil
	// ...
	}
	return m, nil
}

func newStyles(isDark bool) styles {
	lightDark := lipgloss.LightDark(isDark)
	return styles{
		title: lipgloss.NewStyle().
			Foreground(lightDark(lipgloss.Color("#333333"), lipgloss.Color("#EEEEEE"))),
	}
}
```

- **Nothing blocks.** The terminal's reply comes back through the normal input reader, so keystrokes aren't lost.
- **It runs once, at startup.** Store the result in the model and rebuild styles only when a new `BackgroundColorMsg` arrives. If you want to re-check later (for example, after the user switches the terminal theme), return `tea.RequestBackgroundColor` from `Update` again.
- **Plan for no reply.** Some terminals never answer. Start with a sensible default (usually dark) so the UI looks fine until the message arrives, or if it never does.

## Or detect before the program starts

If you'd rather have a synchronous answer, call it once in `main` before Bubble Tea takes over the terminal:

```go
isDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)
p := tea.NewProgram(model{isDark: isDark, styles: newStyles(isDark)})
```

That's safe because nothing else is reading stdin yet. Never call it once the program is running. The message-based approach is still the better choice, because it handles terminals that don't reply and lets you re-check later.
