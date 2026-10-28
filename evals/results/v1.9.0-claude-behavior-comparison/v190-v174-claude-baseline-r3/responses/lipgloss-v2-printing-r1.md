No. In Lip Gloss v2, `fmt.Println(style.Render(msg))` sends raw ANSI escape codes no matter where the output goes.

## Why

In v1, the renderer checked the terminal and downsampled colors inside `Render`. v2 removed that. `Style.Render` is now a pure function that always emits full-fidelity escape sequences. Downsampling and stripping now happen when you write the output, and `fmt.Println` doesn't do that step. So:

- **Piped** (`mycli | less`, `> out.txt`): the file or pipe gets literal `\x1b[38;2;...m` sequences.
- **`NO_COLOR=1`**: ignored, so colors still print.
- **Limited terminals** (256-color, 16-color, `TERM=dumb`): get truecolor codes they may render wrong.

## Fix

Use Lip Gloss's own print functions. They wrap the output in a `colorprofile` writer that detects the right color profile for the destination:

```go
lipgloss.Println(style.Render(msg))            // stdout
lipgloss.Fprintln(os.Stderr, style.Render(msg)) // stderr, etc.
lipgloss.Printf("%s\n", style.Render(msg))
```

If you write to your own `io.Writer`, or print a lot and want one writer, wrap it yourself:

```go
import "github.com/charmbracelet/colorprofile"

w := colorprofile.NewWriter(os.Stdout, os.Environ())
fmt.Fprintln(w, style.Render(msg))
```

With either approach:
- **Pipe or non-TTY output** gets all ANSI stripped, so it's plain text.
- **`NO_COLOR`** drops colors but keeps text attributes like bold and underline.
- **`CLICOLOR_FORCE`**, `TERM`, and the terminal's actual color support are respected, and colors are downsampled to match.

## Other things to check

- **Layout still applies.** Padding, margins, widths and borders are plain characters, so they still show up in piped output. That's usually fine. If you want truly bare output for scripts, check yourself whether stdout is a terminal (e.g. `term.IsTerminal(os.Stdout.Fd())` from `charmbracelet/x/term`) and skip the styling.
- **Adaptive light/dark colors** are no longer automatic in standalone v2 use. Detect the background once and pick colors from it:
  ```go
  hasDark := lipgloss.HasDarkBackground(os.Stdin, os.Stdout)
  lightDark := lipgloss.LightDark(hasDark)
  fg := lightDark(lipgloss.Color("#333"), lipgloss.Color("#eee"))
  ```
- **Inside Bubble Tea** you don't need any of this, because the program's renderer handles color profiles. This only affects standalone printing like yours.

The quickest change is to replace `fmt.Println` with `lipgloss.Println`. You can test it with `NO_COLOR=1 mycli` and `mycli | cat -v`. With the fix, `cat -v` should show no `^[[` sequences.
