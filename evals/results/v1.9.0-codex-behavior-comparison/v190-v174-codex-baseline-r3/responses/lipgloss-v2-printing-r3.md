**Use `lipgloss.Println` instead.** In Lipgloss v2, `Style.Render()` emits ANSI styling without checking stdout or `NO_COLOR`. `fmt.Println` writes those escape sequences unchanged. citeturn966194search0

```go
import "charm.land/lipgloss/v2"

lipgloss.Println(style.Render(msg))
```

Lipgloss’s output writer handles terminal detection, color downsampling, and `NO_COLOR`. For ordinary piped or redirected output, it strips ANSI sequences. With `NO_COLOR`, colors are disabled; attributes such as bold may remain on a terminal. citeturn966194search5turn767873search5

If you need to keep `fmt`, wrap stdout once:

```go
out := colorprofile.NewWriter(os.Stdout, os.Environ())
fmt.Fprintln(out, style.Render(msg))
```

Here `colorprofile` is `github.com/charmbracelet/colorprofile`. citeturn767873search0