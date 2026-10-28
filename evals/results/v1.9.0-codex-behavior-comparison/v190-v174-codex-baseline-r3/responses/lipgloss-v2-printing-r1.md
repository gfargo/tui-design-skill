**Use `lipgloss.Println` instead.** In Lipgloss v2, `style.Render(msg)` produces ANSI styling without adapting it to stdout. `fmt.Println` writes those bytes directly, so escape sequences can leak into pipes and colors can remain despite `NO_COLOR`.

```go
import "charm.land/lipgloss/v2"

lipgloss.Println(style.Render(msg))
```

Lipgloss’s print functions handle terminal detection and color conversion at output time:

- **Piped stdout:** strips ANSI sequences by default, unless color is explicitly forced.
- **`NO_COLOR=1`:** removes colors; other attributes such as bold may remain on a terminal.
- **Color terminal:** adapts colors to its supported profile.

For another destination, use `lipgloss.Fprintln(os.Stderr, style.Render(msg))`.

This output-time handling is a [v2 behavior](https://github.com/charmbracelet/lipgloss/blob/main/UPGRADE_GUIDE_V2.md); advice about v1’s automatic handling inside `Render` doesn’t apply.