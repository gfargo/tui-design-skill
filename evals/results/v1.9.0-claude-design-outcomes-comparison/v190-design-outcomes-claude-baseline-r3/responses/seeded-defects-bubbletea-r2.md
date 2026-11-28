Not ready to merge yet. The two biggest problems are that a refresh freezes the whole UI, and that the layout assumes an 80×∞ terminal and trusts whatever text the API sends. Here are the problems from most to least serious, followed by a revised version.

## Problems

### 1. The HTTP request blocks the event loop (critical)
`Update` runs on Bubble Tea's only event loop. `http.Get` blocks it, so while the request runs, nothing redraws, resizes are ignored and even `ctrl+c` does nothing. `http.Get` uses `http.DefaultClient`, which has **no timeout**. If the CI API hangs, the app hangs with it until someone kills it.

**Fix:** Do I/O inside a `tea.Cmd` that returns a message. Use a client with a timeout. Ignore `r` while a fetch is already running so requests can't stack up.

### 2. Errors are swallowed and `ok` can be wrong
- The `Decode` error is ignored, so bad JSON still sets `m.ok = true`.
- `resp.StatusCode` is never checked. A 500 or an HTML login page decodes badly, the error is dropped, and the dot turns green.
- It decodes directly into `m.rows`, so a failed decode can leave a partial list on screen.
- The error is never shown, so the user just sees a red dot with no explanation.

**Fix:** Decode into a local slice. Only replace `m.rows` on success. Keep the old rows on failure. Store the error and display it.

### 3. Two states aren't enough
`ok` defaults to `false`, so the app starts with a red dot before anything has gone wrong. It can't tell apart "never loaded", "loading", "failed" and "ok". `Init` also returns `nil`, so the screen stays empty until someone happens to press `r`.

**Fix:** Use a status enum (`loading/ok/err`) and start a fetch in `Init`.

### 4. The fixed width of 80 breaks small tmux panes
In a 50-column pane, the 80-character rule wraps onto two lines, and every long `Detail` wraps across several. The layout falls apart.

**Fix:** Handle `tea.WindowSizeMsg`, store the width and height, and draw everything to that width. Truncate each cell to its column width, measuring display width rather than bytes. `%-20s` pads by rune count, so CJK text and emoji will misalign. It also never truncates, so a long `Name` pushes `Detail` out of place.

### 5. Untrusted text from the API goes straight to the terminal (security)
`Detail` is free text from a remote API. It can contain `\n`, `\r` and `\t`, which wreck the layout. It can also contain ANSI or OSC escape sequences that recolor the screen, move the cursor, change the window title or create fake hyperlinks. That is a terminal-injection risk.

**Fix:** Clean `Name` and `Detail` once when the data arrives: strip escape sequences, turn whitespace runs into single spaces and drop other control characters. Clean the error text before showing it too. Also limit how much of the response body you read.

### 6. No height handling or scrolling, and `cursor` is never used
If there are more rows than the pane is tall, the top scrolls off, separator included. `cursor` is declared but nothing moves it or draws it.

**Fix:** Add `up`/`down` (`k`/`j`), keep a scroll `offset`, draw only the rows that fit, and highlight the selected row. Keep the cursor in range whenever the row list or the window size changes.

### 7. Status is shown by color alone
A red or green `●` means nothing to colorblind users, on monochrome terminals or with `NO_COLOR` set. **Fix:** Put a text label next to it, such as `● ok · 12 pipelines` or `● error: …`, and add a short key-help line.

### 8. Minor issues
- `s +=` in a loop: use `strings.Builder`.
- The style is rebuilt on every `View`: define styles once at package level.
- There's no empty state. With zero rows you get a separator and a dot; show "No pipelines" instead.
- The imports are missing. I assume you trimmed them for the paste; if not, this won't compile.

## Revised version

```go
package main

import (
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
	pipelinesURL = "https://ci.example.com/api/pipelines"
	maxBody      = 10 << 20 // 10 MiB
	maxNameWidth = 20
)

var (
	client = &http.Client{Timeout: 10 * time.Second}

	okStyle       = lipgloss.NewStyle().Foreground(lipgloss.Color("2"))
	errStyle      = lipgloss.NewStyle().Foreground(lipgloss.Color("1"))
	dimStyle      = lipgloss.NewStyle().Faint(true)
	selectedStyle = lipgloss.NewStyle().Reverse(true)
)

type status int

const (
	statusLoading status = iota
	statusOK
	statusErr
)

type pipelinesMsg struct {
	rows []row
	err  error
}

func fetchPipelines() tea.Msg {
	resp, err := client.Get(pipelinesURL)
	if err != nil {
		return pipelinesMsg{err: err}
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return pipelinesMsg{err: fmt.Errorf("unexpected status: %s", resp.Status)}
	}

	var rows []row
	if err := json.NewDecoder(io.LimitReader(resp.Body, maxBody)).Decode(&rows); err != nil {
		return pipelinesMsg{err: fmt.Errorf("decode response: %w", err)}
	}
	for i := range rows {
		rows[i].Name = sanitize(rows[i].Name)
		rows[i].Detail = sanitize(rows[i].Detail)
	}
	return pipelinesMsg{rows: rows}
}

// sanitize makes remote text safe to print on a single line: it strips
// escape sequences, collapses whitespace, and drops control characters.
func sanitize(s string) string {
	s = strings.Join(strings.Fields(ansi.Strip(s)), " ")
	return strings.Map(func(r rune) rune {
		if unicode.IsControl(r) {
			return -1
		}
		return r
	}, s)
}

// fit truncates s to w display cells and pads it to exactly w.
func fit(s string, w int) string {
	s = ansi.Truncate(s, w, "…")
	return s + strings.Repeat(" ", max(0, w-ansi.StringWidth(s)))
}

type model struct {
	rows   []row
	status status
	err    error
	cursor int
	offset int
	width  int
	height int
}

func newModel() model { return model{status: statusLoading} }

func (m model) Init() tea.Cmd { return fetchPipelines }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height

	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "r":
			if m.status == statusLoading {
				return m, nil
			}
			m.status = statusLoading
			return m, fetchPipelines
		case "up", "k":
			m.cursor--
		case "down", "j":
			m.cursor++
		}

	case pipelinesMsg:
		if msg.err != nil {
			// Keep the last good rows on screen.
			m.status, m.err = statusErr, msg.err
		} else {
			m.status, m.err, m.rows = statusOK, nil, msg.rows
		}
	}

	m.clamp()
	return m, nil
}

// listHeight is the number of rows that fit between the rule and the status line.
func (m model) listHeight() int { return max(1, m.height-2) }

func (m *model) clamp() {
	m.cursor = max(0, min(m.cursor, len(m.rows)-1))
	h := m.listHeight()
	if m.cursor < m.offset {
		m.offset = m.cursor
	}
	if m.cursor >= m.offset+h {
		m.offset = m.cursor - h + 1
	}
	m.offset = max(0, min(m.offset, len(m.rows)-h))
}

func (m model) View() string {
	if m.width == 0 {
		return "" // wait for the first WindowSizeMsg
	}

	var b strings.Builder
	b.WriteString(dimStyle.Render(strings.Repeat("─", m.width)) + "\n")

	nameW := min(maxNameWidth, m.width/3)
	detailW := max(0, m.width-nameW-1)

	switch {
	case len(m.rows) == 0 && m.status == statusLoading:
		b.WriteString(dimStyle.Render(fit("Loading pipelines…", m.width)) + "\n")
	case len(m.rows) == 0:
		b.WriteString(dimStyle.Render(fit("No pipelines.", m.width)) + "\n")
	default:
		end := min(len(m.rows), m.offset+m.listHeight())
		for i := m.offset; i < end; i++ {
			r := m.rows[i]
			line := fit(r.Name, nameW) + " " + fit(r.Detail, detailW)
			if i == m.cursor {
				line = selectedStyle.Render(line)
			}
			b.WriteString(line + "\n")
		}
	}

	b.WriteString(ansi.Truncate(m.statusLine(), m.width, "…"))
	return b.String()
}

func (m model) statusLine() string {
	var s string
	switch m.status {
	case statusLoading:
		s = "◌ loading…"
	case statusOK:
		s = okStyle.Render("●") + fmt.Sprintf(" ok · %d pipelines", len(m.rows))
	case statusErr:
		s = errStyle.Render("●") + " error: " + sanitize(m.err.Error())
	}
	return s + dimStyle.Render("  r refresh · ↑/↓ move · q quit")
}
```

## Notes on the changes
- **`fetchPipelines` is a plain `func() tea.Msg`.** That already satisfies `tea.Cmd`, so it can be returned directly. Bubble Tea runs it in its own goroutine.
- **Only one fetch runs at a time.** The `r` key is ignored while loading. If you add auto-refresh on a timer later, also put a request ID on `pipelinesMsg` and drop responses that arrive late.
- **Text is cleaned once, when it arrives,** not on every `View`, so drawing stays cheap. `ansi.Truncate` and `ansi.StringWidth` measure on-screen width, so wide characters line up and styled status text truncates without breaking escape codes.
- **Long `Detail` text:** since you now have a cursor, a natural next step is a footer or an `enter` view that shows the selected row's full `Detail` wrapped to `m.width`. Truncated rows alone can hide the information people need.
- **Small panes:** below about 3 rows tall the list still gets one line and may push the separator off screen. That seems fine for a pane that small, but say if you'd rather show a "pane too small" message.
- **Versions:** this targets Bubble Tea v1 (`tea.KeyMsg`, string `View`) and Go 1.21+ for the built-in `min`/`max`.

I haven't compiled or run this, since I only had the snippet. Please build it and try it in a narrow pane before you merge.
