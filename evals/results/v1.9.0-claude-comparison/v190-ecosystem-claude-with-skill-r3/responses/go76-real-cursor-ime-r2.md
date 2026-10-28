I checked the skill's Bubble Tea reference. Here's the cause and the fix.

**Why it happens:** In v2, `textinput` draws a "virtual" cursor, which is just a styled cell, and keeps the terminal's real cursor hidden. The IME candidate window doesn't see the styled cell. It opens wherever the real cursor is, and since your program never placed that cursor, it's sitting at the bottom-left. (Screen readers track the real cursor too, so this change helps them as well.)

**Fix:** Turn off the virtual cursor and place the real one through the `tea.View`:

```go
m.input = textinput.New()
m.input.SetVirtualCursor(false) // the terminal cursor is the caret now
m.input.Focus()                 // Cursor() returns nil while blurred

// In View
func (m model) View() tea.View {
    v := tea.NewView("Search\n" + m.input.View())
    if c := m.input.Cursor(); c != nil {
        c.Y++ // Cursor() is relative to the input; add the input's offset in the frame
        v.Cursor = c
    }
    return v
}
```

Three things to get right:

1. **Add the input's offset to the cursor position.** `Cursor()` gives a position relative to the input. Add however many lines sit above the input (title, header, list) to `c.Y`, and add any left border, padding or column offset to `c.X`. If you skip this, the IME window opens near the input but not on the caret.
2. **Only set it while the input is focused.** `Cursor()` returns nil when the input is blurred, so the nil check handles that. When a modal or overlay covers the input, blur the input. Otherwise the caret and IME window appear on top of the overlay.
3. **Japanese hits a width bug.** As of bubbles v2.2.1, `textinput.Cursor()` counts **runes, not terminal cells**. Each full-width kana or kanji takes 2 cells, so the caret falls one cell further behind for every wide character before it. After you type 日本語, the IME window opens 3 cells too far left. (`textarea` counts cells correctly, so it doesn't have this problem.) If the field doesn't scroll sideways, you can correct for it like this:

   ```go
   import "github.com/charmbracelet/x/ansi"

   if c := m.input.Cursor(); c != nil {
       before := []rune(m.input.Value())[:m.input.Position()]
       c.X += ansi.StringWidth(string(before)) - len(before) // add the extra cell for each wide rune
       c.Y += inputRow
       v.Cursor = c
   }
   ```

   This correction assumes the whole value is visible. Once the text is longer than the field and it scrolls, the input's internal scroll offset isn't exposed, so the math will be off. For long Japanese text, either switch to a one-line `textarea`, or set the input's `Width` large enough that it doesn't scroll. Also check whether a newer bubbles release has fixed the rune/cell counting before you add this workaround.

**To verify:** Type mixed text like `abc日本語` in a pinned-size test frame and check that the cursor X equals the cell width (3 + 6 = 9, plus the prompt width), not the rune count (6). Then test by hand with the macOS Japanese IME in your users' terminal, and inside tmux too. tmux passes the cursor position through, but it only gets it right if your app placed the cursor itself.
