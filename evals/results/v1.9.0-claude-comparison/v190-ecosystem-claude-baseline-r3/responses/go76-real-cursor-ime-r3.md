## Why the candidate window appears in the wrong place

The terminal's IME draws the candidate window wherever the terminal's own cursor is. It knows nothing about your UI.

By default, the Bubbles v2 `textinput` uses a **virtual cursor**: it draws a styled block character where the cursor should be, and Bubble Tea hides the real terminal cursor. The real cursor is left wherever the renderer stopped drawing, which is usually the bottom-left of your program's output. That's where the IME opens its window.

## The fix: use the real cursor and position it yourself

1. Turn off the virtual cursor on the input.
2. In `View()`, get the input's cursor position, shift it by where the input sits on screen, and set it on the `tea.View`.

```go
func initialModel() model {
	ti := textinput.New()
	ti.Placeholder = "入力してください"
	ti.SetVirtualCursor(false) // use the real terminal cursor
	ti.Focus()
	return model{textInput: ti}
}

func (m model) View() tea.View {
	header := m.headerView()
	body := lipgloss.JoinVertical(lipgloss.Left,
		header,
		m.textInput.View(),
		m.footerView(),
	)

	v := tea.NewView(body)

	if !m.textInput.VirtualCursor() {
		c := m.textInput.Cursor() // position relative to the input itself
		if c != nil {
			// Shift it by where the input is drawn on screen.
			c.Y += lipgloss.Height(header)
			// c.X += leftOffset // add this if the input is indented, bordered, padded, etc.
		}
		v.Cursor = c
	}
	return v
}
```

## Things to watch for

- **The offset has to be right.** `textInput.Cursor()` gives a position relative to the input's top-left corner. Add everything rendered above it (headers, margins, top borders) to `Y`, and everything to its left (padding, left borders, side panes) to `X`. If the offset is wrong, the candidate window still shows up, just in the wrong spot.
- **Wide characters are handled.** The input computes `X` from display width, so full-width kana and kanji count as 2 columns.
- **Only the focused input should set a cursor.** If you have several inputs, set `v.Cursor` from the focused one and leave it `nil` otherwise. A `nil` cursor hides it.
- **Styling.** With the real cursor, its look comes from `ti.Styles.Cursor` (color, shape, blink) instead of the virtual cursor's block style.
- **Terminal support varies.** Most modern terminals put the IME at the cursor (iTerm2, WezTerm, kitty, Ghostty, Windows Terminal, GNOME Terminal). A few older or minimal ones ignore the cursor position. Nothing in the app can fix that.

If you share your `View()` and layout code, I can work out the exact X/Y offsets for you.
