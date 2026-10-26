package bubblesv2

import (
	"image/color"
	"testing"

	"charm.land/bubbles/v2/help"
	tea "charm.land/bubbletea/v2"
)

func TestSettersReplaceExportedFields(t *testing.T) {
	m := newModel()
	if m.viewport.Width() != 80 || m.viewport.Height() != 24 {
		t.Fatalf("viewport = %dx%d, want 80x24", m.viewport.Width(), m.viewport.Height())
	}
	m = m.update(tea.WindowSizeMsg{Width: 100, Height: 30})
	if m.help.Width() != 100 || m.viewport.Width() != 100 || m.viewport.Height() != 28 {
		t.Fatalf("help %d, viewport %dx%d", m.help.Width(), m.viewport.Width(), m.viewport.Height())
	}
	if m.list.Width() != 100 || m.list.Height() != 28 {
		t.Fatalf("list = %dx%d, want 100x28", m.list.Width(), m.list.Height())
	}
}

func TestBackgroundMessageRestylesBubbles(t *testing.T) {
	m := newModel()
	darkR, _, _, _ := m.help.Styles.ShortKey.GetForeground().RGBA() // help.New() defaults to dark
	m = m.update(tea.BackgroundColorMsg{Color: color.White})
	lightR, _, _, _ := m.help.Styles.ShortKey.GetForeground().RGBA()
	wantR, _, _, _ := help.DefaultStyles(false).ShortKey.GetForeground().RGBA()
	if lightR != wantR || lightR == darkR {
		t.Fatalf("help key color r=%d, want light variant %d (dark was %d)", lightR, wantR, darkR)
	}
}
