**Use `lipgloss.Println(style.Render(msg))` instead.** In Lipgloss v2, rendering and output adaptation are separate:

```go
import "charm.land/lipgloss/v2"

lipgloss.Println(style.Render(msg))
```

`style.Render` produces ANSI styling without detecting the output terminal. `fmt.Println` writes those bytes unchanged, so color escapes can leak into pipes or remain when `NO_COLOR` is set.

Lipgloss’s print helpers handle terminal color capabilities, downsampling, and disabling color for redirected output and `NO_COLOR`.

For your one-shot CLI:

- Keep results on stdout and diagnostics on stderr.
- Use plain, stable output for JSON or other machine formats.
- Remember that removing color preserves layout: borders, padding, and wrapping remain. Offer plain output if those would hinder scripts.
- Verify redirected output and `NO_COLOR=1` contain no unwanted escape sequences.