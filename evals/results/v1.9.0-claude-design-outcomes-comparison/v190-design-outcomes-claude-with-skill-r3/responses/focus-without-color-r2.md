Focus is now shown by the border style, which doesn't depend on color. The focused pane gets `=` top and bottom edges. Unfocused panes keep `-`. This is the ASCII version of the usual thin-to-heavy border swap, so it still shows up when colors are off and in plain-text screenshots.

**Files focused:**

```
+=======================+ +--------------------------------------+
| Files                 | | Preview                              |
| > main.go             | | package main                         |
|   util.go             | |                                      |
|   README.md           | | func main() {                        |
+=======================+ +--------------------------------------+
```

**Preview focused:**

```
+-----------------------+ +======================================+
| Files                 | | Preview                              |
| > main.go             | | package main                         |
|   util.go             | |                                      |
|   README.md           | | func main() {                        |
+-----------------------+ +======================================+
```

**Why it works this way:**

- **The border is the only focus cue.** Color, bold and reverse video all disappear in a plain-text screenshot. The border shape is the one thing that survives. The rest of the screen stays exactly the same, so the frames line up and only the edges move when focus changes.
- **The `>` stays when Files loses focus.** It marks which file the Preview pane is showing, not where focus is. Because of that, it shouldn't change with focus. Otherwise people would read two signals for one state.
- **Extra cues for color terminals.** You can add the accent color and a bold title on the focused pane, and reverse video on the selected row only in that pane. Keep that to one color cue plus the border. `NO_COLOR` turns off color only, so bold and reverse still show in the terminal. They just don't show up in the docs.
- **Unicode terminals.** Draw the focused pane with `┏━┓ ┃ ┗━┛` and the others with `┌─┐ │ └─┘`. Use the `+=+` / `+-+` version shown above when the locale isn't UTF-8 or the user passes `--ascii`.

**In code:** make the border style a semantic token instead of a hardcoded value. `border.focus` is `=` (or heavy) plus the accent color, and `border.normal` is `-` (or thin). Choose between them from the app's focus state when rendering, not inside each pane. Add golden-frame tests for both focus states with `NO_COLOR=1`, so the focus cue can't be lost again without a test failing.

**Small terminals:** this layout is 66 columns wide, so it won't fit in a 60-column tmux split. Below that width, show only the focused pane and add a one-line header like `[1 Files] 2 Preview`, with Tab to switch panes. The brackets then mark focus, which also works without color.
