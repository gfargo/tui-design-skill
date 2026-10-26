package listfilter

import (
	"testing"

	"charm.land/bubbles/v2/list"
	tea "charm.land/bubbletea/v2"
)

func newModel() model {
	items := []list.Item{item("apple"), item("quince")}
	return model{list: list.New(items, list.NewDefaultDelegate(), 40, 10)}
}

func press(m model, k tea.KeyPressMsg) (model, tea.Cmd) {
	next, cmd := m.Update(k)
	return next.(model), cmd
}

func isQuit(cmd tea.Cmd) bool {
	if cmd == nil {
		return false
	}
	_, ok := cmd().(tea.QuitMsg)
	return ok
}

func TestQIsTextWhileFiltering(t *testing.T) {
	m, _ := press(newModel(), tea.KeyPressMsg{Code: '/', Text: "/"})
	if m.list.FilterState() != list.Filtering {
		t.Fatalf("state = %v, want Filtering", m.list.FilterState())
	}
	m, cmd := press(m, tea.KeyPressMsg{Code: 'q', Text: "q"})
	if isQuit(cmd) {
		t.Fatal("q quit the app while the user was typing into the filter")
	}
	if got := m.list.FilterValue(); got != "q" {
		t.Fatalf("filter value = %q, want %q", got, "q")
	}
}

func TestQQuitsWhenBrowsing(t *testing.T) {
	if _, cmd := press(newModel(), tea.KeyPressMsg{Code: 'q', Text: "q"}); !isQuit(cmd) {
		t.Fatal("q should quit when the list is not filtering")
	}
}

func TestCtrlZSuspendsEvenWhileFiltering(t *testing.T) {
	m, _ := press(newModel(), tea.KeyPressMsg{Code: '/', Text: "/"})
	_, cmd := press(m, tea.KeyPressMsg{Code: 'z', Mod: tea.ModCtrl})
	if cmd == nil {
		t.Fatal("expected a suspend command")
	}
	if _, ok := cmd().(tea.SuspendMsg); !ok {
		t.Fatal("expected tea.SuspendMsg")
	}
}
