The IME draws its candidate window wherever the terminal's real cursor is. By default the v2 `textinput` draws a fake cursor: it styles a character cell inside the rendered string. The real terminal cursor stays hidden and parked somewhere else, which is often the bottom-left after a render. The fix is to switch to the real cursor and tell Bubble Tea where it goes.

I didn't find your code in the working directory, so here is the general pattern.

## 1. Turn off the virtual cursor

```go
ti := textinput.New()
ti.SetVirtualCursor(false) // use the real terminal cursor
ti.Focus()
```

## 2. Return the cursor position from `View()`

In v2, `View()` returns a `tea.View`, and its `Cursor` field puts the real cursor on screen. `ti.Cursor()` gives you a `*tea.Cursor`. Its position is relative to the textinput's own output, and it's `nil` when the input is blurred or using the virtual cursor.

```go
func (m model) View() tea.View {
	header := "Enter your name:\n\n"
	body := header + m.input.View()

	v := tea.NewView(body)

	if c := m.input.Cursor(); c != nil {
		// Shift from textinput-local coordinates to screen coordinates
		c.Y += lipgloss.Height(header) - 1 // number of lines rendered above the input
		// c.X += leftOffset                // add this if the input sits after a border, padding, or other text
		v.Cursor = c
	}
	return v
}
```

## Offsets

`Cursor()` already accounts for the prompt and the text width (including double-width CJK characters). It doesn't know anything about your layout, so you need to add:
- **Y**: how many lines are rendered above the input (headers, borders, top padding, margins).
- **X**: how many columns are to its left (left border, padding, side-by-side panes). If it's inside a `lipgloss.NewStyle().Border(...).Padding(0, 1)` box, that's `+1` for the border and `+1` for the padding on X, and `+1` on Y for the top border.

If the offset is wrong, the candidate window will show up near the input but not on it. That's the easiest way to check the math: type something with the IME and see where the window opens.

## Notes

- Hide the cursor when nothing is focused. `Cursor()` returns `nil` when the input is blurred, so the `if` above already handles that.
- If you want a particular cursor look, set `c.Shape` (`tea.CursorBlock`, `tea.CursorBar`, `tea.CursorUnderline`) and `c.Blink`. Cursor styling now comes from the terminal instead of a lipgloss style.
- `textarea` works the same way: `SetVirtualCursor(false)` plus `ta.Cursor()`.

If you share your `View()` and layout code, I can work out the exact offsets for you.
