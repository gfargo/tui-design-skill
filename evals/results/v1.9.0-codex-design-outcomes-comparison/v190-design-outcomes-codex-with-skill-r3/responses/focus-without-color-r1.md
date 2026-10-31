Mark the active pane’s title with `[focus]`. Keep `>` for the selected file, so selection and keyboard focus remain distinct without color.

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

`Tab` / `Shift+Tab` switches focus, moving the title marker. This adds one focus cue, no extra borders, and no repeated row markers.

At 80×24, retain both panes. In a 60-column split, show only the focused pane; `Tab` switches the visible pane:

```text
+----------------------------------------------------------+
| Files [focus]                                            |
| > main.go                                                |
|   util.go                                                |
|   README.md                                              |
+----------------------------------------------------------+
Tab: Preview
```

Truncate long content to fit. Below the minimum needed for a title and one content row, display `Terminal too small`.