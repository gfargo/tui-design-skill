package bubbles

import (
	"strings"
	"testing"

	"charm.land/bubbles/v2/help"
	tea "charm.land/bubbletea/v2"
)

func TestQuitBindingQuits(t *testing.T) {
	_, cmd := keysModel{}.Update(tea.KeyPressMsg{Code: 'q', Text: "q"})
	if cmd == nil {
		t.Fatal("expected a quit command")
	}
	if _, ok := cmd().(tea.QuitMsg); !ok {
		t.Fatal("expected tea.QuitMsg")
	}
}

func TestHelpRendersBindings(t *testing.T) {
	if view := help.New().View(keys); !strings.Contains(view, "quit") {
		t.Fatalf("help view %q is missing the quit binding", view)
	}
}
