The stutter comes from `lipgloss.HasDarkBackground` competing with Bubble Tea for the terminal. It's meant for standalone Lip Gloss programs, not for use inside a running Bubble Tea program.

## Why it stutters

`HasDarkBackground` sends a background-color query (OSC 11) to the terminal. It then **reads the reply from stdin and waits for it**, with a timeout. Inside `Update` that causes two problems:

1. **It blocks the event loop.** `Update` runs on Bubble Tea's main loop, so nothing else is processed while it waits. That includes rendering and key handling.
2. **It competes with Bubble Tea's input reader.** Bubble Tea is already reading stdin. The two readers grab each other's bytes, so you lose keystrokes, or parts of the terminal's reply show up as junk key events. Calling it on every `Update` makes this worse.

## The Bubble Tea v2 way: ask with a command, handle the reply as a message

Bubble Tea v2 can send this query for you and deliver the answer as a message. Request it once in `Init`, store the result, and build your styles from it:

```go
import (
	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

type model struct {
	isDark bool
	styles styles
}

func newModel() model {
	m := model{isDark: true} // sensible default in case the terminal never answers
	m.styles = newStyles(m.isDark)
	return m
}

func (m model) Init() tea.Cmd {
	return tea.RequestBackgroundColor
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.BackgroundColorMsg:
		m.isDark = msg.IsDark()
		m.styles = newStyles(m.isDark) // rebuild once, not every frame
		return m, nil
	// ...
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
			Foreground(lightDark(lipgloss.Color("#333333"), lipgloss.Color("#EEEEEE"))),
	}
}
```

(If you're on the older module path, the imports are `github.com/charmbracelet/bubbletea/v2` and `github.com/charmbracelet/lipgloss/v2`.)

## Key points

- **Query once, usually in `Init`.** Don't query per update or per render. Send `tea.RequestBackgroundColor` again only if you have a reason to think the background changed.
- **Always set a default theme.** Some terminals (and some tmux/SSH setups) never answer, so the message may never arrive. Start with a default (dark is a common choice) and switch if the reply comes.
- **Keep styles in the model.** Build them once when `BackgroundColorMsg` arrives, not in `View`.
- **Keep blocking I/O out of `Update`.** This applies to anything slow: wrap it in a `tea.Cmd` so it runs off the event loop and comes back as a message.

You only need `lipgloss.HasDarkBackground(os.Stdin, os.Stdout)` in plain Lip Gloss programs that aren't running Bubble Tea, where nothing else is reading stdin.
