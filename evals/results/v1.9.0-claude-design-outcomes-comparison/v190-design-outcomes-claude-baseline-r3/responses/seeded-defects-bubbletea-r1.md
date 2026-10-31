Several of these will cause real trouble: the UI freezes during refresh, errors get swallowed, the layout breaks in small panes, and the API can write raw escape sequences to the user's terminal. Here they are roughly by severity, then a revised version.

## Problems

### 1. The HTTP call blocks the event loop
`Update` runs on Bubble Tea's main loop. While `http.Get` waits, nothing redraws and no keys are handled, including `q` and `ctrl+c`. `http.Get` also uses the default client, which has **no timeout**, so a stuck CI API hangs the app for good.

**Fix:** Do the I/O in a `tea.Cmd` that returns a message, and use an `http.Client` with a `Timeout`. `Update` should only change state.

### 2. Errors are swallowed and a bad response can corrupt state
- The return value of `Decode` is ignored. If decoding fails, `ok` is still set to `true`.
- The status code is never checked. A 500 or 401 with an HTML or JSON error body counts as success, or decodes into garbage.
- Decoding straight into `m.rows` means a failed decode can leave the slice half-overwritten.
- The response size is unbounded.

**Fix:** Check `resp.StatusCode`, decode into a local variable, and wrap the body in `io.LimitReader`. Only replace `m.rows` on success. On failure, keep the old rows (stale data is better than none) and store the error.

### 3. One `ok` bool can't represent the real states
At startup `ok` is `false`, so the dot shows red ("error") before anything has been fetched. There's no loading state and no error message, so the user can't tell "never fetched", "fetching", "failed: 401" and "fine" apart.

**Fix:** Use a status enum (`loading / ok / err`) plus an `err` field, and show the error text.

### 4. `Init` doesn't fetch anything
The first screen is empty with a red dot until the user happens to press `r`.

**Fix:** Return the fetch command from `Init`.

### 5. The width is hardcoded and the window size is ignored
In a pane narrower than 80 columns, the separator wraps onto two lines and long rows wrap unpredictably. There's no handling for height either, so with more rows than lines the top scrolls off and can't be reached.

**Fix:** Handle `tea.WindowSizeMsg`, store `width` and `height`, and lay everything out from those values. Render nothing meaningful until the first size message arrives.

### 6. `Detail` is untrusted free text sent straight to the terminal
- **Escape sequences:** If `Detail` (or `Name`) contains `\x1b[...`, the CI API can recolor, move the cursor, clear the screen, or set the window title in the user's terminal. Treat it as hostile input.
- **Newlines and tabs** break the "one row per line" layout and throw off any height calculation.
- **Length:** Long strings wrap and break the layout.

**Fix:** Strip control characters (this neutralizes ESC), replace `\n`, `\r` and `\t` with spaces, then truncate to the available width with an ellipsis.

### 7. `%-20s` pads by rune count, not display width
Wide characters (CJK, emoji) push columns out of line, and names longer than 20 characters aren't cut off, so they shift the detail column.

**Fix:** Measure with `ansi.StringWidth` and truncate with `ansi.Truncate` (from `github.com/charmbracelet/x/ansi`). Make the name column shrink in narrow panes.

### 8. `cursor` exists but does nothing
No keys move it, nothing renders it, and nothing clamps it after a refresh changes the row count.

**Fix:** Add up/down keys (with `j`/`k`), clamp the cursor after every refresh, keep a scroll `offset` so the cursor stays visible, and highlight the selected row.

### 9. Repeated `r` presses run overlapping fetches
Once fetching is async, holding `r` starts many requests, and they can finish out of order.

**Fix:** Ignore `r` while a fetch is already running. If you later want manual refresh to cancel the current fetch, tag each request with an ID and drop responses that are out of date.

### 10. The status is shown only by color
A red/green dot is the most common colorblind confusion, and it tells you nothing with `NO_COLOR` set or in a monochrome terminal.

**Fix:** Put a text label next to it, and use a different glyph for loading.

### 11. Smaller issues
- Building the string with `+=` in a loop is quadratic. Use `strings.Builder`.
- There's no empty state. "0 pipelines" should be shown explicitly.
- The snippet won't compile as pasted (no imports, `row` isn't defined). That's probably just trimming, but check it.

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

const pipelinesURL = "https://ci.example.com/api/pipelines"

var client = &http.Client{Timeout: 10 * time.Second}

type status int

const (
	statusLoading status = iota
	statusOK
	statusErr
)

type model struct {
	rows   []row
	status status
	err    error
	cursor int
	offset int
	width  int
	height int
}

type rowsMsg struct {
	rows []row
	err  error
}

func newModel() model { return model{status: statusLoading} }

func fetchRows() tea.Msg {
	resp, err := client.Get(pipelinesURL)
	if err != nil {
		return rowsMsg{err: err}
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return rowsMsg{err: fmt.Errorf("HTTP %s", resp.Status)}
	}
	var rows []row
	if err := json.NewDecoder(io.LimitReader(resp.Body, 10<<20)).Decode(&rows); err != nil {
		return rowsMsg{err: fmt.Errorf("decode: %w", err)}
	}
	return rowsMsg{rows: rows}
}

func (m model) Init() tea.Cmd { return fetchRows }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
		m.clampScroll()

	case rowsMsg:
		if msg.err != nil {
			m.status, m.err = statusErr, msg.err // keep stale rows visible
		} else {
			m.status, m.err, m.rows = statusOK, nil, msg.rows
		}
		m.clampScroll()

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
			m.clampScroll()
		case "down", "j":
			m.cursor++
			m.clampScroll()
		}
	}
	return m, nil
}

// listHeight is the number of rows available below the status line and separator.
func (m model) listHeight() int { return max(1, m.height-2) }

func (m *model) clampScroll() {
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

// sanitize makes untrusted API text safe for a single terminal line:
// whitespace control chars become spaces, all other control chars
// (including ESC, so no escape sequences survive) are dropped.
func sanitize(s string) string {
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

func fit(s string, w int) string {
	s = ansi.Truncate(sanitize(s), w, "…")
	return s + strings.Repeat(" ", max(0, w-ansi.StringWidth(s)))
}

var (
	okStyle       = lipgloss.NewStyle().Foreground(lipgloss.Color("2"))
	errStyle      = lipgloss.NewStyle().Foreground(lipgloss.Color("1"))
	dimStyle      = lipgloss.NewStyle().Faint(true)
	selectedStyle = lipgloss.NewStyle().Reverse(true)
)

func (m model) statusLine() string {
	var s string
	switch m.status {
	case statusLoading:
		s = dimStyle.Render("◌ loading…")
	case statusOK:
		s = okStyle.Render("●") + fmt.Sprintf(" ok · %d pipelines", len(m.rows))
	case statusErr:
		s = errStyle.Render("✗") + " error: " + sanitize(m.err.Error())
	}
	return ansi.Truncate(s, m.width, "…")
}

func (m model) View() string {
	if m.width == 0 {
		return "loading…" // no WindowSizeMsg yet
	}

	var b strings.Builder
	b.WriteString(m.statusLine() + "\n")
	b.WriteString(strings.Repeat("─", m.width) + "\n")

	if len(m.rows) == 0 && m.status != statusLoading {
		b.WriteString(dimStyle.Render("no pipelines"))
		return b.String()
	}

	nameW := min(20, max(8, m.width/3))
	detailW := max(0, m.width-nameW-1)

	end := min(len(m.rows), m.offset+m.listHeight())
	for i := m.offset; i < end; i++ {
		r := m.rows[i]
		line := fit(r.Name, nameW) + " " + fit(r.Detail, detailW)
		if i == m.cursor {
			line = selectedStyle.Render(line)
		}
		b.WriteString(line)
		if i < end-1 {
			b.WriteString("\n")
		}
	}
	return b.String()
}
```

## Notes on the fix
- **Pure `View`:** All scroll and cursor clamping happens in `Update`, so `View` only reads state.
- **Ellipsis:** Long `Detail` is cut at the pane edge with `…`. If people need the full text, add an `enter` key that opens the selected row in a `bubbles/viewport` with wrapping, rather than wrapping inside the list.
- **Refresh during a fetch:** `r` is ignored while loading, which avoids races without request IDs. If you'd rather a new `r` cancel the current fetch, pass a `context.Context` to the command and cancel it on the next press.
- **Testing:** Run it in a pane around 40×10 and feed it a fixture where `Detail` contains `\x1b[2J`, newlines and emoji. Those inputs break the original version.
