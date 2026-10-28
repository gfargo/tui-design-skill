The candidate window shows up bottom-left because of how `textinput` draws its caret. By default it paints a fake caret (a styled cell) and leaves the real terminal cursor hidden. Bubble Tea parks that hidden cursor in a corner, and the OS IME places its candidate window at the real cursor. Screen readers follow the real cursor too.

The fix is to turn off the fake caret and give the input's real cursor position to Bubble Tea through the view.

## Fix

```go
m.input = textinput.New()
m.input.SetVirtualCursor(false) // the real terminal cursor becomes the caret
m.input.Focus()

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

Three rules:

- **Add the input's offset.** `Cursor()` gives a position relative to the input. Add the rows above it (titles, borders, padding) to `Y`, and anything to its left to `X`. If you skip this, the caret and candidate window land on the wrong row.
- **Nil means hidden.** `Cursor()` returns nil while the input is blurred. When a modal or other overlay covers the input, blur it so the caret doesn't blink through the overlay.
- **Set `v.Cursor` on every frame the input is focused.** The view is rebuilt each frame, so a position set once is lost on the next render.

## Japanese text needs a width fix

As of v2.2.1, `textinput.Cursor()` counts **runes**, not terminal **cells**. Each full-width character (kana, kanji, emoji) takes 2 cells, so the caret falls one cell further behind the text for each one. After `日本語`, the candidate window would appear 3 cells too far left. You have two options:

**1. Correct X yourself.** This works when the input's `Width` is 0 or wide enough that the text never scrolls sideways:

```go
import "github.com/charmbracelet/x/ansi"

if c := m.input.Cursor(); c != nil {
    r := []rune(m.input.Value())
    pos := m.input.Position() // caret position, in runes
    c.X += ansi.StringWidth(string(r[:pos])) - pos // add the extra cells taken by wide runes
    c.Y++
    v.Cursor = c
}
```

If the text does scroll sideways, this correction is wrong: the scroll offset is private, so you can't tell which runes are on screen.

**2. Use a one-line `textarea` instead.** `textarea.Cursor()` already counts cells. Set its height to 1, turn off line numbers, and remap Enter (`KeyMap.InsertNewline`) so it submits instead of adding a new line. For input that is mostly Japanese, this is the more reliable choice.

## Check it

Use a real IME (macOS Japanese input or fcitx/ibus) and try these:
- Type `にほんご` and convert it: the candidate window should sit at the caret.
- Move left and right through the mixed text `abc日本語def`: the caret should stay on the right character.
- Open and close any overlay: the caret should hide while it's open and come back afterwards.

Terminals differ in how well they track the cursor during IME composition. iTerm2, WezTerm, kitty and Ghostty handle it; some multiplexer setups don't. If it works in one terminal but not another, try it outside tmux before blaming your code.
