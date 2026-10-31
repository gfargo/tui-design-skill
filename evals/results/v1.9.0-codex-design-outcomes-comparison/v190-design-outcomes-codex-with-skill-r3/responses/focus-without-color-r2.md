Add `[focus]` to the active pane’s title. Keep `>` as the selected-file marker, so selection and keyboard focus have distinct meanings.

Files focused:

```text
+-----------------------+ +--------------------------------------+
| Files [focus]         | | Preview                              |
| > main.go             | | package main                         |
|   util.go             | |                                      |
|   README.md           | | func main() {                        |
+-----------------------+ +--------------------------------------+
Tab: switch pane
```

Preview focused:

```text
+-----------------------+ +--------------------------------------+
| Files                 | | Preview [focus]                      |
| > main.go             | | package main                         |
|   util.go             | |                                      |
|   README.md           | | func main() {                        |
+-----------------------+ +--------------------------------------+
Tab: switch pane
```

These use literal ASCII characters; focus survives removal of all terminal styling. Exactly one pane has `[focus]`, and Tab moves both keyboard input and that label.

At 80×24, retain both panes. In a 60-column split, show only the focused pane; Tab switches views while preserving selection and scroll position:

```text
+----------------------------------------------------------+
| Files [focus]                                            |
| > main.go                                                |
|   util.go                                                |
|   README.md                                              |
+----------------------------------------------------------+
Tab: Preview
```

Clutter audit: one border layer, one focus cue, and one selected-row marker. No extra borders or repeated row markers. Keep content truncation within pane bounds; below the supported minimum, show `Terminal too small` with the required dimensions.