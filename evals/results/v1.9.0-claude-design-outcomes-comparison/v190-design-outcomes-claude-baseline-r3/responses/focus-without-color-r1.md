I couldn't change the code. The working directory is empty (no source files, not even hidden ones), and in this session I can only read and search files, not write them. So below is the design, with the exact screens it should produce. If you point me at the TUI source, I can show where the change goes.

## The fix

The focused pane is currently marked only by color, so it disappears under NO_COLOR. The fix is to mark focus with different characters, which show up with or without color. Colors can still be added on top.

1. **Border characters.** The focused pane draws `=` across the top and bottom and `#` for the sides and corners. Unfocused panes keep `-`, `|` and `+`. Every line stays the same width, so nothing shifts when focus moves.
2. **Title brackets.** The focused pane's title is shown as `[Files]`. Unfocused titles stay plain. This still works in a screenshot that has been cropped or shrunk.
3. **List cursor.** `>` means "this pane has the keyboard and this is the selected row." When Files loses focus, its cursor becomes `-`. You can still see which file is being previewed, but it no longer looks like it takes input.

## Files pane focused

```
#=======================# +--------------------------------------+
# [Files]               # | Preview                              |
# > main.go             # | package main                         |
#   util.go             # |                                      |
#   README.md           # | func main() {                        |
#=======================# +--------------------------------------+
```

## Preview pane focused

```
+-----------------------+ #======================================#
| Files                 | # [Preview]                            #
| - main.go             | # package main                         #
|   util.go             | #                                      #
|   README.md           | # func main() {                        #
+-----------------------+ #======================================#
```

## Implementation notes

- Pick the border character set and the title format from the focus state alone. Don't check NO_COLOR for this, so focus looks the same with color on or off.
- Each title gets 2 extra characters for the brackets, so pad it to the same inner width. Don't let the brackets push the right border out.
- If you later switch to Unicode box-drawing, use `═║╔╗╚╝` for the focused pane and `─│┌┐└┘` for the others. Keep the ASCII version as a fallback for terminals that can't show Unicode.
- Re-take the docs screenshots in both focus states so readers can see the difference.
