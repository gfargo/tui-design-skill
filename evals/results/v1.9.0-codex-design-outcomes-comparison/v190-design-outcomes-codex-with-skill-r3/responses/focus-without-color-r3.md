Mark only the focused pane’s title with `[focus]`. This survives disabled colors and plain-text screenshots. Keep `>` for the selected file, so selection and keyboard focus remain distinct.

Files focused:

```text
+-----------------------+ +--------------------------------------+
| Files [focus]         | | Preview                              |
| > main.go             | | package main                         |
|   util.go             | |                                      |
|   README.md           | | func main() {                        |
+-----------------------+ +--------------------------------------+
```

Preview focused:

```text
+-----------------------+ +--------------------------------------+
| Files                 | | Preview [focus]                      |
| > main.go             | | package main                         |
|   util.go             | |                                      |
|   README.md           | | func main() {                        |
+-----------------------+ +--------------------------------------+
```

`Tab` / `Shift+Tab` switches focus without changing the selected file.

At 80×24, retain both panes. In a 60-column split, show only the focused pane, with both names available as tabs:

```text
Files [focus]   Preview
> main.go
  util.go
  README.md
Tab: switch pane
```

```text
Files   Preview [focus]
package main

func main() {
Tab: switch pane
```

The clutter budget stays small: one border layer, one focus cue, and one selected-row marker. No extra border decoration or repeated row markers are needed. Truncate long content to the available width; below 24 columns or 6 rows, show `Terminal too small`.