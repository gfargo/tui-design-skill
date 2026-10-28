No. In Lipgloss v2, `fmt.Println(style.Render(msg))` writes raw ANSI escape codes no matter where the output goes.

## Why

In v1, the renderer checked the terminal and environment for you. v2 removed that, so `Style.Render` is now a pure function: it always returns the full styled string, with true-color sequences and all. It doesn't know whether stdout is a TTY or whether `NO_COLOR` is set. In v2, the output step is where colors get reduced or removed.

So with your current code:

- **Piped** (`mycli | less`, `> out.txt`): escape codes end up in the file or pipe.
- **`NO_COLOR=1`**: ignored, so colors still print.
- **Limited terminals** (256-color or 16-color): true-color codes aren't reduced to fit.

## Fix

Use Lipgloss's print functions instead of `fmt`. They wrap the writer in a `colorprofile` writer, which detects what the output supports and reduces or removes styling to match:

```go
lipgloss.Println(style.Render(msg))              // stdout
lipgloss.Fprintln(os.Stderr, errStyle.Render(e)) // stderr
s := lipgloss.Sprint(style.Render(msg))          // string, reduced to fit stdout
```

If you write a lot of output, or write through your own `io.Writer`, wrap it once:

```go
w := colorprofile.NewWriter(os.Stdout, os.Environ())
fmt.Fprintln(w, style.Render(msg))
```

The detection respects TTY status, `NO_COLOR`, `CLICOLOR` / `CLICOLOR_FORCE`, `TERM=dumb`, and the terminal's color depth. Piped output gets all ANSI removed. `NO_COLOR` removes colors, though I believe text attributes like bold may still come through.

## Related v2 gotcha: adaptive colors

`AdaptiveColor` is also gone from the core package, because Lipgloss no longer checks the terminal background on its own. If you use light/dark colors, detect the background yourself:

```go
hasDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)
lightDark := lipgloss.LightDark(hasDark)
style := lipgloss.NewStyle().Foreground(lightDark(lipgloss.Color("#333"), lipgloss.Color("#eee")))
```

For a non-interactive CLI, it's reasonable to skip the background query when stdout isn't a TTY and just default to dark. That avoids sending terminal queries when output is piped.

**Quick check:** run `mycli | cat -v`. If you see `^[[` sequences, escape codes are leaking. Then run `NO_COLOR=1 mycli` and confirm the colors are gone.
