I didn't find any code to change: the working directory is empty. So I haven't edited anything. Below is the design, which you can apply once you point me at the source.

## The fix

Right now, color is the only thing that shows which pane has focus, so the cue disappears when colors are off. Each pane needs to show focus in a way that doesn't depend on color:

1. **Border style.** The focused pane's border changes from `+ - |` to `# = #`. This is the strongest cue, because you can see it at a glance even from across the room.
2. **Title marker.** The focused pane's title is wrapped in brackets, like `[Files]`. This still works if a screen reader or copy-paste drops the borders.
3. **Cursor only in the focused pane.** `>` means "keys go here." When the Files pane loses focus, its selected file is marked `*` instead. You can still see which file is being previewed, but the pane no longer looks like it's taking input.

**Files focused:**

```
#=======================# +--------------------------------------+
# [Files]               # | Preview                              |
# > main.go             # | package main                         |
#   util.go             # |                                      |
#   README.md           # | func main() {                        |
#=======================# +--------------------------------------+
```

**Preview focused:**

```
+-----------------------+ #======================================#
| Files                 | # [Preview]                            #
| * main.go             | # package main                         #
|   util.go             | #                                      #
|   README.md           | # func main() {                        #
+-----------------------+ #======================================#
```

Both panes stay the same width and height whichever one has focus, so the layout doesn't shift when focus moves. If your terminals and docs can show Unicode, heavy box-drawing characters (`┏━┓┃┗━┛`) for the focused pane and light ones (`┌─┐│└─┘`) for the other look cleaner and work the same way.

## Implementation sketch

The `.go` filenames suggest Bubble Tea/Lip Gloss. If so, the change would look roughly like this:

```go
func paneStyle(focused bool) lipgloss.Style {
	s := lipgloss.NewStyle().Border(lipgloss.NormalBorder())
	if focused {
		s = s.Border(lipgloss.ThickBorder()) // or a custom # = border for ASCII mode
	}
	return s // keep color as an extra cue on top of this, not the only one
}

func paneTitle(name string, focused bool) string {
	if focused {
		return "[" + name + "]"
	}
	return name
}

// in the file list:
marker := "  "
if i == m.selected {
	marker = "* "
	if m.focus == focusFiles {
		marker = "> "
	}
}
```

You can keep the existing focus color. Just add it on top of these cues so it isn't the only signal. Send me the path to the project (or the rendering code) and I'll make the actual edit and check the output with `NO_COLOR=1`.
