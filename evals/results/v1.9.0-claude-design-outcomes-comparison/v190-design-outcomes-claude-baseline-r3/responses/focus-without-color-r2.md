I couldn't make the change because the working directory is empty. There's no source code here, so I haven't edited or run anything. Below is the design I'd use, with the exact plain-text output it should produce. If you point me at the rendering code, I'll implement it.

## The fix

Show focus with characters instead of color, so it still works with NO_COLOR, in plain-text screenshots and in black-and-white docs:

1. **The focused pane gets a heavier border.** Its corners and sides become `#` and its top and bottom become `=`. Unfocused panes keep the light `+ - |` border. Everything stays ASCII, so it renders in any terminal and pastes cleanly into docs.
2. **Only the focused pane shows the `>` cursor.** At the moment, `>` in the Files pane suggests that pane has focus even when it doesn't. When Files loses focus, its selected row should show `*` instead. You can still see which file is selected, but it no longer looks focused.

Both panes keep the same width, so the layout doesn't shift when focus moves. With colors enabled, you can still add color or bold on top, but focus is never shown by color alone.

### Files pane focused

```
#=======================# +--------------------------------------+
# Files                 # | Preview                              |
# > main.go             # | package main                         |
#   util.go             # |                                      |
#   README.md           # | func main() {                        |
#=======================# +--------------------------------------+
```

### Preview pane focused

```
+-----------------------+ #======================================#
| Files                 | # Preview                              #
| * main.go             | # package main                         #
|   util.go             | #                                      #
|   README.md           | # func main() {                        #
+-----------------------+ #======================================#
```

## When implementing

- Choose the border style from focus state alone, not from whether color is on. That way, color and no-color output use the same layout and the docs screenshots match what users see.
- Don't use bold or reverse video as the only cue. Some terminals still show them with NO_COLOR, but they disappear from plain-text screenshots.
- If you add more panes later, this still works because only one pane has the `#`/`=` border at a time.
