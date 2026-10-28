No—**Lipgloss v2’s `Style.Render` does not detect terminal capabilities or honor `NO_COLOR` itself.** It produces styled ANSI text, and `fmt.Println` writes that text unchanged, including into pipes.

For your standalone CLI, use Lipgloss’s output helper:

```go
import "charm.land/lipgloss/v2"

lipgloss.Println(style.Render(msg))
```

That applies output color-profile detection, including non-TTY output and `NO_COLOR`, and downsamples colors for the terminal.

Keep two distinctions in mind:

- Removing color doesn’t remove borders, padding, or wrapping. For stable machine output, provide plain text or JSON without decorative styles.
- Results belong on stdout; diagnostics belong on stderr. Detect capabilities for the stream you actually write to.

Verify the built CLI with redirected stdout and with `NO_COLOR=1`; check that output contains no unwanted escape sequences and still communicates meaning without color.