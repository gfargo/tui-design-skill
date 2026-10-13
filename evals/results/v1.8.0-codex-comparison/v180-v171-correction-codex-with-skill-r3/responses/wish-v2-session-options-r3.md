No—`bubbletea.MakeRenderer(sess)` is a **v1 helper removed in Wish v2**. In v2, Lipgloss creates styled strings, and Bubble Tea handles color downsampling for each client.

Use Wish’s session-specific options when constructing the program:

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/wish/v2/bubbletea"
)

// Inside your session handler:
p := tea.NewProgram(newModel(), bubbletea.MakeOptions(sess)...)
```

`MakeOptions(sess)` configures input, output, and color-profile detection for the **SSH client’s PTY**. If you already use `bubbletea.Middleware`, it applies these options automatically.

Render Lipgloss styles normally inside `View()` and return them through `tea.NewView(...)`. Avoid detecting the server’s profile or forcing a global profile.

For client-specific **light/dark palettes**, separately return `tea.RequestBackgroundColor` from `Init()`, handle `tea.BackgroundColorMsg` in `Update()`, and choose colors with `lipgloss.LightDark(msg.IsDark())`. Keep a default palette because some clients never answer the query.