The candidate window appears in the bottom-left because Bubble Tea v2's `textinput` doesn't move the real terminal cursor. By default it draws a **virtual cursor**, which is just a styled cell, and leaves the real cursor hidden wherever the last render left it. That's usually the bottom-left. IME candidate windows (and screen readers) follow the real cursor, not the styled cell.

## Fix: hand the caret to the real cursor

```go
m.input = textinput.New()
m.input.SetVirtualCursor(false) // the terminal cursor is the caret now
m.input.Focus()                 // Cursor() returns nil while blurred
```

Then set the cursor on the view in `View`:

```go
func (m model) View() tea.View {
    header := "Search"
    v := tea.NewView(header + "\n" + m.input.View())

    if c := m.input.Cursor(); c != nil {
        // Cursor() is relative to the input, so add the input's offset in the frame
        c.Y += lipgloss.Height(header) // rows above the input
        // c.X += <cells to the left of the input: borders, padding, side panes>
        v.Cursor = c
    }
    return v
}
```

Three things to get right:

1. **Offsets.** `Cursor()` gives a position inside the input. Add every row above the input and every cell to its left (borders, padding, a sidebar). If you skip this, the popup still lands in the wrong place, just closer.
2. **Focus.** `Cursor()` is nil while the input is blurred, so the cursor gets hidden. Blur the input when a modal or overlay covers it, or the caret will blink on top of the overlay.
3. **Wide characters, which matter for Japanese.** In v2.2.1, `textinput.Cursor()` counts **runes, not cells**. Each full-width character (あ, 漢, and so on) takes 2 cells, so after typing `日本語` the caret sits 3 cells too far left. The candidate window drifts further from the text with every character. (`textarea` counts cells correctly.) You can correct it yourself:

```go
import "github.com/charmbracelet/x/ansi"

if c := m.input.Cursor(); c != nil {
    before := []rune(m.input.Value())[:m.input.Position()]
    c.X += ansi.StringWidth(string(before)) - len(before) // runes → cells
    c.Y += lipgloss.Height(header)
    v.Cursor = c
    }
```

   This assumes the input isn't horizontally scrolled. Give it a width wide enough for typical input. If the text overflows and scrolls, the correction should only count the visible part before the caret, and `textinput` doesn't expose its scroll offset. If you need long CJK input, a one-line `textarea` avoids this because it already counts cells.

## Checking it

Run the program in a terminal that reports IME position, such as iTerm2, WezTerm, kitty, Ghostty or Terminal.app. Type some kana, start a conversion, and check that the candidate window sits under the caret. Do it again after several kanji to confirm the wide-character correction holds. Also open any overlay to check that the caret disappears while the input is blurred.

This comes from the skill's Bubble Tea reference (`references/ecosystem-go.md:335`). I haven't run this snippet against your code, so check the import paths against your module versions.
