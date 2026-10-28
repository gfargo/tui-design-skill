No, not in v2. This changed from v1.

## Why it breaks

In Lipgloss v2, `style.Render()` is pure. It always returns the full escape sequences for your styles, including true color, and never checks the terminal. v2 moved color detection and downsampling to **output time**. `fmt.Println` writes those bytes as-is, so:

- **Piped/redirected** (`mycli | less`, `> out.txt`): the output contains raw `\x1b[38;2;...m` sequences.
- **`NO_COLOR=1`**: ignored, colors still print.
- **Older terminals** (256 or 16 colors): they get true-color codes they may render badly.

## The fix

Print with Lipgloss's writer helpers instead of `fmt`:

```go
lipgloss.Println(style.Render(msg))               // stdout
lipgloss.Fprintln(os.Stderr, style.Render(msg))   // stderr
s := lipgloss.Sprint(style.Render(msg))           // if you need the string
```

These go through `charmbracelet/colorprofile`. It detects the profile from the writer and environment (TTY or not, `NO_COLOR`, `CLICOLOR_FORCE`, `TERM`, etc.) and then downsamples or strips the escape codes:

- Not a TTY: all ANSI is stripped, so you get plain text.
- `NO_COLOR`: colors are removed. Text decorations like bold may remain.
- 256 or 16 colors: colors are converted to the nearest supported value.

If you write through your own `io.Writer`, wrap it once:

```go
w := colorprofile.NewWriter(os.Stdout, os.Environ())
fmt.Fprintln(w, style.Render(msg))
```

## Related gotchas

1. **Adaptive colors:** v2 doesn't detect the background color automatically. Use `lipgloss.LightDark(isDark)`. In a non-interactive CLI, only call `lipgloss.HasDarkBackground(os.Stdin, os.Stdout)` when stdout is a TTY. It queries the terminal, so it can stall or return garbage when piped. Otherwise default to dark (or light).
2. **Layout still applies:** padding, borders, `Width`, and alignment don't use escape codes, so they still show up in piped output. Usually that's what you want. If it's machine-readable output (for example `--json` or `--plain`), skip Lipgloss entirely.
3. **Pick one stream per message:** errors go to stderr through `lipgloss.Fprintln(os.Stderr, ...)`. That way stderr gets its own TTY check. `mycli 2>err.log` then stays clean while stdout keeps its colors.

In short, replace `fmt.Println(style.Render(x))` with `lipgloss.Println(style.Render(x))` everywhere and piping and `NO_COLOR` will work.
