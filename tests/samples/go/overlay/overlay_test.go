package overlay

import (
	"regexp"
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

var sgr = regexp.MustCompile(`\x1b\[[0-9;:]*m`)

func lines(v tea.View) []string {
	return strings.Split(sgr.ReplaceAllString(v.Content, ""), "\n")
}

func click(t *testing.T, v tea.View, x, y int) tea.Msg {
	t.Helper()
	cmd := v.OnMouse(tea.MouseClickMsg{X: x, Y: y, Button: tea.MouseLeft})
	if cmd == nil {
		t.Fatalf("click at (%d,%d) returned no Cmd", x, y)
	}
	return cmd()
}

func TestDialogCompositesOverBaseAndHitTests(t *testing.T) {
	m := model{width: 30, height: 9, body: "base text", dialog: "Delete?"}
	v := m.View()
	got := lines(v)
	if len(got) != 9 || lipgloss.Width(v.Content) > 30 {
		t.Fatalf("frame is %dx%d, want 9 rows within 30 columns", lipgloss.Width(v.Content), len(got))
	}
	if !strings.HasPrefix(got[0], "base text") {
		t.Fatalf("base layer missing from row 0: %q", got[0])
	}
	row := -1
	for i, l := range got {
		if strings.Contains(l, "Delete?") {
			row = i
		}
	}
	if row < 0 {
		t.Fatal("dialog text not drawn over the base")
	}
	col := strings.Index(got[row], "Delete?")
	if id := click(t, v, col, row); id != hitMsg("dialog") {
		t.Fatalf("click on the dialog hit %v, want dialog", id)
	}
	if id := click(t, v, 0, 0); id != hitMsg("base") {
		t.Fatalf("click outside the dialog hit %v, want base", id)
	}
	if v.OnMouse(tea.MouseWheelMsg{X: 0, Y: 0}) != nil {
		t.Fatal("only clicks should produce a Cmd")
	}
}

func TestNoDialogMeansBaseOnly(t *testing.T) {
	v := model{width: 30, height: 9, body: "base text"}.View()
	if id := click(t, v, 15, 4); id != hitMsg("base") {
		t.Fatalf("hit %v, want base", id)
	}
}
