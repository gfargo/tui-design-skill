package firstframe

import (
	"strings"
	"testing"

	"charm.land/bubbles/v2/spinner"
	tea "charm.land/bubbletea/v2"
)

func TestInitStartsSpinnerAndTimer(t *testing.T) {
	m := newModel()
	batch, ok := m.Init()().(tea.BatchMsg)
	if !ok || len(batch) != 2 {
		t.Fatalf("Init should batch the spinner Tick and the timer Init, got %T", m.Init()())
	}
	tick, ok := batch[0]().(spinner.TickMsg)
	if !ok {
		t.Fatal("first Cmd should be the spinner Tick")
	}
	before := m.spinner.View()
	next, cmd := m.Update(tick)
	m = next.(model)
	if m.spinner.View() == before {
		t.Fatalf("spinner did not advance past %q", before)
	}
	if cmd == nil {
		t.Fatal("Update must return the spinner's next tick or the animation stops")
	}
}

func TestPlaceholderUntilFirstWindowSize(t *testing.T) {
	m := newModel()
	if got := m.View().Content; got != "loading…" {
		t.Fatalf("before WindowSizeMsg View = %q, want the placeholder", got)
	}
	next, _ := m.Update(tea.WindowSizeMsg{Width: 40, Height: 10})
	m = next.(model)
	if m.list.Width() != 40 || m.list.Height() != 9 {
		t.Fatalf("list = %dx%d, want 40x9", m.list.Width(), m.list.Height())
	}
	if got := m.View().Content; strings.Contains(got, "loading") || !strings.Contains(got, "one") {
		t.Fatalf("after WindowSizeMsg View should show the list, got %q", got)
	}
}
