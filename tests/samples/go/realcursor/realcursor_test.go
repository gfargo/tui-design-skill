package realcursor

import "testing"

func TestViewPlacesTheRealCursorAtTheCaret(t *testing.T) {
	m := newModel()
	m.input.SetValue("héllo")
	c := m.View().Cursor
	if c == nil {
		t.Fatal("View set no cursor")
	}
	if c.X != 7 || c.Y != 1 { // "> " prompt + 5 runes, one title line above
		t.Fatalf("cursor at (%d,%d), want (7,1)", c.X, c.Y)
	}
}

// Documents a v2.2.1 limitation the reference warns about: textinput counts
// runes, not cells, so each wide rune leaves the real cursor one cell short.
func TestTextinputCursorCountsRunesNotCells(t *testing.T) {
	m := newModel()
	m.input.SetValue("日本語")
	if c := m.View().Cursor; c.X != 2+3 { // the caret really sits at 2+6
		t.Fatalf("cursor X = %d; if textinput now counts cells (want 8), drop the warning from the reference", c.X)
	}
}

func TestBlurredInputHidesTheCursor(t *testing.T) {
	m := newModel()
	m.input.Blur()
	if m.View().Cursor != nil {
		t.Fatal("a blurred input must leave v.Cursor nil so the cursor is hidden")
	}
}

func TestVirtualCursorLeavesTheRealOneUnset(t *testing.T) {
	m := newModel()
	m.input.SetVirtualCursor(true)
	if m.input.Cursor() != nil {
		t.Fatal("with the virtual cursor on, Cursor() must be nil")
	}
}
