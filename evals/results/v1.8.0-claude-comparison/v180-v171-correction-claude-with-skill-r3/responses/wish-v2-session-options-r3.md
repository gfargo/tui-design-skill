You shouldn't call `bubbletea.MakeRenderer(sess)`. That helper is from Wish v1 and was removed in v2. In v1, Lipgloss wrote to the terminal itself, so each session needed its own renderer. In v2, Lipgloss only builds styled strings, and Bubble Tea writes them to the terminal and reduces the colors to what that terminal supports. So the per-session setting now goes on the Bubble Tea program, through `bubbletea.MakeOptions(sess)`.

## Simple case: let the middleware do it

`bubbletea.Middleware` calls `MakeOptions(sess)` for you. That ties input, output and color detection to each client's terminal session (PTY), not to the server process.

```go
import (
    tea "charm.land/bubbletea/v2"
    "charm.land/wish/v2"
    "charm.land/wish/v2/activeterm"
    "charm.land/wish/v2/bubbletea"
    "charm.land/wish/v2/logging"
    // plus the ssh package your Wish v2 version uses for ssh.Session
)

s, err := wish.NewServer(
    wish.WithAddress(":23234"),
    wish.WithHostKeyPath(".ssh/id_ed25519"),
    wish.WithMiddleware(
        bubbletea.Middleware(teaHandler),
        activeterm.Middleware(), // reject sessions without a PTY
        logging.Middleware(),
    ),
)

func teaHandler(sess ssh.Session) (tea.Model, []tea.ProgramOption) {
    pty, _, _ := sess.Pty()
    return newModel(pty.Window.Width, pty.Window.Height), nil
}
```

## If you need your own `tea.WithFilter`

The default middleware adds its own options after yours. `MakeOptions` includes a filter that turns ctrl+z (suspend) into a resume, and it overwrites any filter you set. To keep yours, build the program yourself and chain the two filters:

```go
bubbletea.MiddlewareWithProgramHandler(func(sess ssh.Session) *tea.Program {
    opts := bubbletea.MakeOptions(sess)
    // add your options; if you need a filter, call the one from Wish inside yours
    return tea.NewProgram(newModel(), opts...)
})
```

## What else breaks the per-client setup

1. **Server-side detection.** Don't call `lipgloss.HasDarkBackground(os.Stdin, os.Stdout)`, `lipgloss.Println`, or `colorprofile.Detect(os.Stdout, ...)` inside a session. They all look at the server's terminal, not the client's.
2. **Light/dark theme is a separate question.** The color profile only covers how many colors the client supports. To find out whether its background is dark, return `tea.RequestBackgroundColor` from `Init`, handle `tea.BackgroundColorMsg`, and rebuild your styles with `lipgloss.LightDark(msg.IsDark())`. Show a default palette first, because some terminals never answer.
3. **Keep themed styles in the model, not in package-level globals.** One global theme gets overwritten as different clients connect. Fixed colors are fine globally: `Render` always outputs full truecolor, and each program reduces it for its own client.
4. **Clients often look less capable than they are.** `COLORTERM` usually doesn't make it over SSH, so a truecolor terminal may be detected as 256-color. OpenSSH also only sends environment variables you allow with `SendEnv`/`SetEnv`. Use colors that still read well at 256 and 16 colors, and don't rely on color alone to carry meaning.

**To test it,** connect from clients with different settings, for example `TERM=xterm-256color ssh -p 23234 localhost`, then `TERM=xterm` or `TERM=dumb`. Each session should show different colors from the same server. For golden-file tests, fix the profile with `tea.WithColorProfile(colorprofile.ASCII)` so test output doesn't change from machine to machine.

I took all of this from the skill's Go reference (`references/ecosystem-go.md`, the Wish and Lipgloss sections). I haven't compiled the snippets. Check the ssh `Session` import path against your Wish v2 version, since it isn't one of the `charm.land` packages.
