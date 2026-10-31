The fix is to make focus visible in the border itself instead of in its color. The focused pane gets a heavy border and the other pane keeps the thin one. A color change disappears under `NO_COLOR` and in black-and-white screenshots, but the shape of the border doesn't. You can keep the accent color on the focused border for color users.

**Files focused:**

```
#=======================# +--------------------------------------+
# Files                 # | Preview                              |
# > main.go             # | package main                         |
#   util.go             # |                                      |
#   README.md           # | func main() {                        |
#=======================# +--------------------------------------+
```

**Preview focused:**

```
+-----------------------+ #======================================#
| Files                 | # Preview                              #
| > main.go             | # package main                         #
|   util.go             | #                                      #
|   README.md           | # func main() {                        #
+-----------------------+ #======================================#
```

Why it's built this way:

- **The border only changes its characters.** The heavy border is the same width and height as the thin one, so nothing in the layout moves or reflows when focus changes.
- **ASCII on purpose.** Your screen already uses ASCII borders, so the heavy border is ASCII too (`#` and `=`). When the terminal supports Unicode box drawing, use `┏━┓┃┗━┛` for the focused pane and `┌─┐│└─┘` for the other. Turning colors off doesn't change which characters are drawn, so the Unicode version keeps the cue under `NO_COLOR` too.
- **One cue is enough.** I didn't also add a title marker like `▸ Files` or `[Files]`. Use one non-color cue plus color; adding more just makes the screen busier. Bold on the focused title is fine to keep, but it doesn't show in plain-text docs or in terminals that ignore bold, so it can't be the only cue.
- **The `>` stays in Files when Preview has focus.** It shows which file is being previewed, not where the keyboard is. In color mode, show the selection in reverse video only in the focused pane and muted in the other. In plain text the border carries the focus signal, so the `>` doesn't have to.

To keep this working, add golden-frame tests at a fixed terminal size with `NO_COLOR=1` set: one with Files focused and one with Preview focused. Each test should check which pane has the `#`/`=` border, or `┏━┓` in Unicode mode. If someone later turns focus back into a color-only change, these tests fail.

If you tell me the framework (Bubble Tea/Lipgloss, Ratatui, Textual, Ink…) and point me at the rendering code, I can make the change there.
