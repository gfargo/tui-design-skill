**Use `lipgloss.Println` instead.** In Lipgloss v2, `style.Render` produces ANSI styling without checking the output terminal or `NO_COLOR`. `fmt.Println` writes those bytes unchanged, so escape sequences can leak into pipes and files.

```go
import "charm.land/lipgloss/v2"

lipgloss.Println(style.Render(msg))
```

Lipgloss’s printing helpers handle output color-profile detection and downsampling, including non-TTY output and `NO_COLOR`.

For a one-shot CLI, also:

- Keep results on stdout and diagnostics on stderr; detect color support per destination.
- Keep machine output such as `--json` entirely unstyled.
- Remember that removing ANSI doesn’t remove borders, padding, or wrapping—use a separate plain format when needed.
- Test redirected output and `NO_COLOR=1`, checking that no ANSI escapes appear.