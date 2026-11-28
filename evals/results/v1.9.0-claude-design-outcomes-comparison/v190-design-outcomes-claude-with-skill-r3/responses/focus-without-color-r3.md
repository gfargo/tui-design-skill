Focus is shown by border weight now, so it doesn't depend on color at all. The focused pane gets a heavy border (`#` corners and sides, `=` top and bottom) and the other pane keeps the light `+ - |` border. Nothing else on the screen changes and no extra labels are added.

**Files focused**

```
#=======================# +--------------------------------------+
# Files                 # | Preview                              |
# > main.go             # | package main                         |
#   util.go             # |                                      |
#   README.md           # | func main() {                        |
#=======================# +--------------------------------------+
```

**Preview focused**

```
+-----------------------+ #======================================#
| Files                 | # Preview                              #
| > main.go             | # package main                         #
|   util.go             | #                                      #
|   README.md           | # func main() {                        #
+-----------------------+ #======================================#
```

**Why this works**
- **Bold and reverse video don't help here.** `NO_COLOR` leaves them on in the terminal, but a plain-text docs screenshot drops them. Only the characters themselves carry through, which means the border.
- **The `>` stays on `main.go` in both states.** It shows which file is being previewed, not which pane has focus. If it disappeared when Preview took focus, users would lose track of what they're reading. In color mode, keep the Files row in reverse video while Files has focus and switch it to dim when Preview does. In plain text that difference disappears, which is fine because the border already shows focus.
- **Each pane's width is unchanged.** Only the border characters change, so nothing shifts when you press Tab.

**Implementation**
- Pick the border style from focus state, not from the theme: `border = focused ? heavy : light`. With color on, also give the focused border the accent color and bold its title. That's one non-color cue plus color, which is enough without making the screen busy.
- In Unicode mode, use `┏━┓┃┗━┛` for the focused pane and `┌─┐│└─┘` for the others. Use the ASCII set shown above when Unicode isn't available, and for docs, since your screenshots are already ASCII.
- Add golden-frame tests for both focus states with `NO_COLOR=1` at 80×24. The test should fail if the two frames come out identical.

**Narrow terminals:** at 60 columns the two panes won't both fit. Show only the focused pane, with a tab row like `[Files]  Preview` above it, and use the brackets as the focus cue there.
