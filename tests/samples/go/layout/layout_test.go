package layout

import (
	"testing"

	tea "charm.land/bubbletea/v2"
)

func TestWindowSizeSplitsPanes(t *testing.T) {
	m := model{}.update(tea.WindowSizeMsg{Width: 90, Height: 30})
	if m.leftPaneWidth != 30 || m.rightPaneWidth != 60 {
		t.Fatalf("panes = %d/%d, want 30/60", m.leftPaneWidth, m.rightPaneWidth)
	}
}
