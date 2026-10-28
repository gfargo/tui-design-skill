I don't see any Bubble Tea code in this directory, so this answer is based on how Bubble Tea v2 and Bubbles v2 behave, not on your code.

## Why it happens

By default the v2 `textinput` uses a **virtual cursor**: it draws the cursor as a styled character inside the rendered string and hides the real terminal cursor. The real cursor stays wherever rendering finished, which is usually the bottom-left of the screen.

The IME doesn't look at your fake cursor. The terminal places the candidate window at the **real** cursor, so it shows up bottom-left.

## Fix: use the real cursor and position it

1. Turn off the virtual cursor on the input.
2. In `View()`, return a `tea.View` with `Cursor` set from `ti.Cursor()`.
3. Shift that position by wherever the input sits in your layout.

```go
func newModel() model {
	ti := textinput.New()
	ti.Placeholder = "入力してください"
	ti.SetVirtualCursor(false) // use the real terminal cursor
	ti.Focus()
	return model{input: ti}
}

func (m model) View() tea.View {
	header := "Name:\n\n"            // anything rendered above the input
	body := header + m.input.View() + "\n\n(esc to quit)"

	v := tea.NewView(body)

	// Cursor() returns nil when the input is blurred or using a virtual cursor.
	if c := m.input.Cursor(); c != nil {
		// c.Position is relative to the input's own top-left (prompt included).
		// Shift it by where the input actually sits on screen.
		c.Position.Y += lipgloss.Height(header) - 1
		c.Position.X += 0 // add any left padding/border/margin here
		v.Cursor = c
	}
	return v
}
```

## Getting the offset right

This is where most bugs come from:

- **Y offset**: the number of lines rendered above the input. `lipgloss.Height(header) - 1` works when the header ends in a newline. Counting lines with `strings.Count(above, "\n")` also works.
- **X offset**: any left border, padding or margin on containers around the input, e.g. `style.GetBorderLeftSize() + style.GetPaddingLeft() + style.GetMarginLeft()`.
- **Multiple inputs**: only set `v.Cursor` for the focused one. The `Cursor()` nil check handles that for you.
- **Width**: `ti.Cursor()` already measures CJK text in display cells (double-width characters), so don't adjust X for the text itself. Only add offsets for layout outside the input.

## Optional styling

The real cursor's look is set through `tea.Cursor` fields (`Shape`, `Blink`, `Color`) or the input's cursor styles, e.g. `c.Shape = tea.CursorBar`.

## Checking the fix

Type a few Japanese characters in iTerm2, Ghostty, kitty or WezTerm. The candidate window should stay next to the caret as it moves. If it's off by a line or a few columns, your Y/X offset is wrong. If it's still bottom-left, `v.Cursor` isn't being set: either `SetVirtualCursor(false)` wasn't called or the input isn't focused.

If you share your `View()`, I can work out the exact offsets for your layout.
