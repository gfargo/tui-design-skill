package lipglosssample

import (
	"testing"

	"charm.land/lipgloss/v2"
)

func TestWidthAndHeightIncludeBorderAndPadding(t *testing.T) {
	out, inner := renderBox()
	if w, h := lipgloss.Width(out), lipgloss.Height(out); w != 20 || h != 5 {
		t.Fatalf("rendered %dx%d, want 20x5 (border and padding inside Width/Height)", w, h)
	}
	if inner != 16 {
		t.Fatalf("text columns = %d, want 16", inner)
	}
}
