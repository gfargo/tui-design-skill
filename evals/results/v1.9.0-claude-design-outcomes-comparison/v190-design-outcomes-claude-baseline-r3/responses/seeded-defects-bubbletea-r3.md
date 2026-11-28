The two biggest problems are that the HTTP call blocks the UI with no timeout, and that `Detail` is printed raw, so a CI-supplied string can inject escape sequences into the terminal. The hardcoded width and the lack of height handling will also break this in small tmux panes. Here's the full list, most serious first, with a fixed version at the end.

## Problems

### 1. Blocking network I/O inside `Update` (critical)
`Update` runs on the event loop. `http.Get` there freezes the whole program: no redraws, no key handling, and even `ctrl+c` won't respond until the request returns. `http.Get` uses `http.DefaultClient`, which has **no timeout**, so a stuck CI API hangs the TUI forever.

**Fix:** Do the fetch in a `tea.Cmd`. Use `http.NewRequestWithContext` with a timeout, and send the result back as a message (`rowsMsg` / `errMsg`). Add a loading state so the user can see a fetch is running, and so pressing `r` repeatedly doesn't start overlapping requests.

### 2. Errors are ignored or reported wrongly
- The `Decode` error is thrown away, and `m.ok = true` runs whether or not decoding worked.
- `resp.StatusCode` is never checked. A 500 or 401 with an HTML body shows as "ok" with empty or partial rows.
- If decoding fails partway, `Decode(&m.rows)` can leave `m.rows` half-overwritten.
- The response body has no size limit.

**Fix:** Check that the status is 200. Decode into a local slice and only assign it on success. Wrap the body in `io.LimitReader`. Keep the error so you can display it.

### 3. `ok bool` can't tell "not loaded yet" from "failed"
At startup `ok` is `false`, so the dot is red before anything has gone wrong. `Init` returns `nil`, so nothing loads until the user presses `r`.

**Fix:** Use a status enum (idle/loading/ok/error) plus `err error`. Start with `loading` and have `Init` return the fetch command.

### 4. Status is shown by color alone
A red or green `●` means nothing to colorblind users, under `NO_COLOR`, or in a monochrome terminal. It also never says *what* failed.

**Fix:** Show text next to the dot: `● ok · 42 pipelines` / `● error: ci api: 503 Service Unavailable`.

### 5. Untrusted API strings go straight to the terminal (security plus layout)
`Detail` (and `Name`) come from CI, so they can contain build output with ANSI escapes, `\r`, `\n`, tabs, or other control characters. That can:
- inject terminal escape sequences (change colors, move the cursor, set the window title, write OSC 52 to the clipboard, etc.)
- break the layout, because one row with a newline turns into several screen lines

**Fix:** Clean the strings once when the data arrives, not on every frame. Strip ANSI sequences, turn newlines and tabs into spaces, and drop all other control characters.

### 6. Hardcoded `width = 80` and no `tea.WindowSizeMsg` handling
In a 50-column tmux pane the 80-character rule wraps onto a second line, and every long `Detail` wraps too, which garbles the screen.

**Fix:** Store `width` and `height` from `tea.WindowSizeMsg`. Size everything from them, and truncate each line to the pane width.

### 7. `%-20s` pads by bytes and never truncates
`%-20s` counts bytes, not terminal columns, so names with CJK characters or emoji misalign. Names longer than 20 characters push the detail column out of line.

**Fix:** Use display-width-aware truncate and pad (`ansi.Truncate` / `ansi.StringWidth`), and shrink the name column on narrow panes.

### 8. No height handling or scrolling, and `cursor` is never used
With more pipelines than pane rows, the top scrolls off and the status line may end up off-screen. `cursor` is declared but never moved or drawn.

**Fix:** Add up/down keys, keep a scroll `offset` so the cursor stays visible, and render only the rows that fit. After a reload, clamp the cursor and offset to the new row count. (`bubbles/table` or `bubbles/viewport` are good options if you'd rather not do this by hand.)

### 9. Minor
- `s +=` in a loop: use `strings.Builder`.
- `defer` inside a `switch` case in `Update` is a sign the I/O is in the wrong place; it goes away with fix 1.
- Imports and the `row` type are missing from the snippet. I assume they exist elsewhere.
- When `r` fails, keep the old rows on screen and show the error. Don't blank the list.

## Fixed version (Bubble Tea v1 API)

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
	"unicode"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/charmbracelet/x/ansi"
)

const (
	apiURL       = "https://ci.example.com/api/pipelines"
	fetchTimeout = 10 * time.Second
	maxBody      = 10 << 20 // 10 MiB
	maxNameWidth = 20
	chromeLines  = 2 // rule + status line
)

type status int

const (
	statusLoading status = iota
	statusOK
	statusErr
)

type (
	rowsMsg struct{ rows []row }
	errMsg  struct{ err error }
)

type model struct {
	rows          []row
	status        status
	err           error
	updated       time.Time
	cursor        int
	offset        int
	width, height int
}

func newModel() model { return model{status: statusLoading} }

func fetchRows() tea.Msg {
	ctx, cancel := context.WithTimeout(context.Background(), fetchTimeout)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, apiURL, nil)
	if err != nil {
		return errMsg{err}
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return errMsg{err}
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return errMsg{fmt.Errorf("ci api: %s", resp.Status)}
	}
	var rows []row
	if err := json.NewDecoder(io.LimitReader(resp.Body, maxBody)).Decode(&rows); err != nil {
		return errMsg{fmt.Errorf("decode: %w", err)}
	}
	for i := range rows {
		rows[i].Name = sanitize(rows[i].Name)
		rows[i].Detail = sanitize(rows[i].Detail)
	}
	return rowsMsg{rows}
}

// sanitize makes untrusted text safe to render on a single line.
func sanitize(s string) string {
	s = ansi.Strip(s)
	return strings.Map(func(r rune) rune {
		switch {
		case r == '\n' || r == '\r' || r == '\t':
			return ' '
		case unicode.IsControl(r):
			return -1
		}
		return r
	}, s)
}

func (m model) Init() tea.Cmd { return fetchRows }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height

	case rowsMsg:
		m.rows = msg.rows
		m.status, m.err, m.updated = statusOK, nil, time.Now()

	case errMsg:
		// Keep stale rows visible; just report the failure.
		m.status, m.err = statusErr, msg.err

	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "r":
			if m.status == statusLoading {
				return m, nil
			}
			m.status = statusLoading
			return m, fetchRows
		case "up", "k":
			m.cursor--
		case "down", "j":
			m.cursor++
		}
	}
	m.clampScroll()
	return m, nil
}

func (m model) bodyHeight() int { return max(m.height-chromeLines, 1) }

func (m *model) clampScroll() {
	m.cursor = max(0, min(m.cursor, len(m.rows)-1))
	h := m.bodyHeight()
	if m.cursor < m.offset {
		m.offset = m.cursor
	}
	if m.cursor >= m.offset+h {
		m.offset = m.cursor - h + 1
	}
	m.offset = max(0, min(m.offset, len(m.rows)-h))
}

// fit truncates or pads s to exactly w terminal cells.
func fit(s string, w int) string {
	t := ansi.Truncate(s, w, "…")
	return t + strings.Repeat(" ", max(w-ansi.StringWidth(t), 0))
}

func (m model) View() string {
	if m.width == 0 {
		return "loading…" // no WindowSizeMsg yet
	}

	var b strings.Builder
	b.WriteString(strings.Repeat("─", m.width) + "\n")

	nameW := min(maxNameWidth, m.width/3)
	detailW := max(m.width-2-nameW-1, 0) // cursor gutter + gap

	end := min(m.offset+m.bodyHeight(), len(m.rows))
	for i := m.offset; i < end; i++ {
		r := m.rows[i]
		gutter := "  "
		if i == m.cursor {
			gutter = "> "
		}
		b.WriteString(gutter + fit(r.Name, nameW) + " " + ansi.Truncate(r.Detail, detailW, "…") + "\n")
	}

	b.WriteString(m.statusLine())
	return b.String()
}

func (m model) statusLine() string {
	var color lipgloss.Color
	var text string
	switch m.status {
	case statusLoading:
		color, text = "8", "loading…"
	case statusOK:
		color = "2"
		text = fmt.Sprintf("ok · %d pipelines · %s", len(m.rows), m.updated.Format("15:04:05"))
	case statusErr:
		color, text = "1", "error: "+m.err.Error()
	}
	dot := lipgloss.NewStyle().Foreground(color).Render("●")
	return dot + " " + ansi.Truncate(sanitize(text), max(m.width-2, 0), "…")
}
```

Notes on the fix:
- Strings are cleaned once inside `fetchRows`, so `View` only truncates. Error text is cleaned too, because error messages can echo server output.
- The scroll offset lives in the model and is adjusted in `Update`. Recomputing it inside `View` makes the list jump as you move the cursor up.
- If you're on Bubble Tea v2, change `tea.KeyMsg` to `tea.KeyPressMsg`. The structure stays the same.
- You could also show a "pane too small" message when `m.width < 30` or `m.height < 3` instead of rendering a cramped layout.
