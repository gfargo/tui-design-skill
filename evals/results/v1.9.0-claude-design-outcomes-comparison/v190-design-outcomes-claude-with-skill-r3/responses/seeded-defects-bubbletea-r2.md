I've read the skill's Go and layout references. Here's the review.

# Review: CI pipelines Bubble Tea model

**Verdict: don't merge yet.** The worst bug is that refreshing freezes the whole program, and Ctrl+C stops working while it's frozen. After that, failures look the same as success, API text goes to the terminal unfiltered, and the layout breaks in exactly the small tmux panes people will use. Issues are listed by how much they hurt users.

## 1. The network call blocks `Update`, so the app freezes and can't be quit

`http.Get` runs inside `Update`. Bubble Tea handles one message at a time, so nothing gets drawn and no key is handled until the request returns. `http.Get` uses the default client, which has **no timeout**. If the CI API hangs, the app hangs too, and `q`/`ctrl+c` are stuck in the queue behind the request.

**Fix:** do the request in a `tea.Cmd` using a client with a timeout. Send the result back as a message, and ignore `r` while a fetch is already running.

## 2. Failures are hidden or reported as success

- The error from `Decode` is ignored. A bad payload still sets `m.ok = true`.
- `resp.StatusCode` is never checked. A 500 or a login page counts as success.
- `Decode(&m.rows)` writes into the existing slice, so a failed decode can leave a mix of old and new rows.
- The `err` value is thrown away. The user only sees a red dot and never learns what went wrong.
- `ok` is a boolean but there are really five states: loading, loaded, empty, error with no data, and error while showing old data.

**Fix:** decode into a new slice, check the status code, and keep both `err` and the time of the last successful fetch. If a refresh fails, keep showing the old rows and label them as stale (see the `status()` function below).

## 3. API text is written to the terminal without filtering

`Detail` is free text from a remote API, and `Name` comes from the same API. Any ANSI escape sequences in either one get run by the user's terminal. That can change colors, move the cursor, set the window title, or write OSC 52 to the clipboard. A `\n` in either one also breaks the row layout.

**Fix:** remove escape sequences and control characters from both fields before rendering. List rows turn newlines into spaces; the detail view keeps them.

## 4. Fixed width and no resize handling break small tmux panes

- `const width = 80` and there's no `tea.WindowSizeMsg` handler. In a 60-column pane, the 80-character rule line wraps onto two lines.
- A long `Detail` wraps across several lines, so you can't tell where one row ends and the next begins.
- `%-20s` pads by code points, not terminal cells. CJK or emoji names won't line up, and names longer than 20 characters aren't cut, so they push into the next column.
- Height is ignored. Once there are more rows than lines, the top rows scroll off and can't be reached.

**Fix:** store the width and height from `WindowSizeMsg`. Cut every cell to a measured cell width with `…`, and only render the rows that fit. Below a set minimum size, show "terminal too small" instead of a broken screen.

## 5. Status is shown by color alone, and it's wrong at startup

- `Init` returns `nil` and `ok` starts as `false`, so the first thing users see is an **empty screen with a red dot**. Nothing has failed; nothing has been fetched yet.
- Red versus green on a `●` is invisible to users with red-green color blindness and means nothing under `NO_COLOR`. `●` is also an ambiguous-width character, so its width varies by terminal.

**Fix:** start a fetch from `Init` and show a loading state. Replace the dot with words, using color only to back them up: `✗ refresh failed…`, `updated 14:03:12`.

## 6. `cursor` is never used and there's no way to read a long `Detail`

`cursor` exists but no key moves it and `View` never draws it. Since `Detail` has to be cut in the list, the full text needs to be reachable somewhere. Nothing on screen tells users that `r` refreshes.

**Fix:** add ↑/↓ (or `k`/`j`) to move, Enter to open a detail view with the full text, Esc to go back, and a footer listing the keys. After a refresh, put the cursor back on the **same pipeline**, not the same index, because refreshed data reorders.

## 7. Smaller issues

- This is the **v1** API (`View() string`, `tea.KeyMsg`). For new code, use v2 (`charm.land/bubbletea/v2`): `View() tea.View` with `v.AltScreen = true`. Bubble Tea v2 also downsamples colors for the terminal, which covers `NO_COLOR`.
- Use the alternate screen. Without it, each frame of a scrolling list ends up in tmux scrollback.
- `s +=` in a loop builds a new string for every row. Use `strings.Builder` and only render the visible rows.
- Color literals (`"1"`, `"2"`) should be named styles (`errStyle`, etc.).

## Clutter count

- **Borders:** 0. Good.
- **Rule line:** 80 cells that carry no information and break at narrow widths. Replace it with the status line.
- **Status signals:** 1 (color). That's one too few. Add a word or symbol.
- **Markers on every row:** none. Good. The selected row should get reverse video and nothing else.

## Behavior at small sizes

The minimum is 40×5: a status line, at least 3 rows, and a footer. The name column takes `min(20, width/3)` cells and `Detail` gets the rest, cut with `…`. Full text is one Enter away.

```
80 columns
Pipelines · 42 · updated 14:03:12
api-build             Waiting for runner: queue depth 14, estimated start i…
web-deploy            Failed: step "migrate" exited 1 after 3m12s; see logs…
↑/↓ move · enter detail · r refresh · q quit

60 columns (tmux split)
Pipelines · 42 · updated 14:03:12
api-build             Waiting for runner: queue depth 14, e…
web-deploy            Failed: step "migrate" exited 1 afte…
↑/↓ move · enter detail · r refresh · q quit

below 40×5
terminal too small: need 40x5
resize, or press q to quit
```

## Suggested rewrite (Bubble Tea v2)

```go
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
	"unicode"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	"github.com/charmbracelet/x/ansi"
)

const (
	apiURL    = "https://ci.example.com/api/pipelines"
	minWidth  = 40
	minHeight = 5 // status + 3 rows + footer
)

var (
	errStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("1"))
	mutedStyle = lipgloss.NewStyle().Faint(true)
	selStyle   = lipgloss.NewStyle().Reverse(true)
	client     = &http.Client{Timeout: 10 * time.Second}
)

type rowsMsg struct {
	rows []row
	err  error
	at   time.Time
}

func fetchRows() tea.Msg {
	resp, err := client.Get(apiURL)
	if err != nil {
		return rowsMsg{err: err}
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return rowsMsg{err: fmt.Errorf("server returned %s", resp.Status)}
	}
	var rows []row
	if err := json.NewDecoder(resp.Body).Decode(&rows); err != nil {
		return rowsMsg{err: fmt.Errorf("bad response: %w", err)}
	}
	return rowsMsg{rows: rows, at: time.Now()}
}

type model struct {
	rows          []row
	cursor        int
	loading       bool
	err           error
	updated       time.Time
	width, height int
	detail        bool
}

func newModel() model { return model{loading: true} }

func (m model) Init() tea.Cmd { return fetchRows }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
	case rowsMsg:
		m.loading, m.err = false, msg.err
		if msg.err == nil {
			m.cursor = reselect(m.rows, m.cursor, msg.rows)
			m.rows, m.updated = msg.rows, msg.at
		}
	case tea.KeyPressMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "esc":
			m.detail = false
		case "enter":
			m.detail = len(m.rows) > 0
		case "up", "k":
			m.cursor = max(m.cursor-1, 0)
		case "down", "j":
			m.cursor = max(min(m.cursor+1, len(m.rows)-1), 0)
		case "r":
			if !m.loading {
				m.loading = true
				return m, fetchRows
			}
		}
	}
	return m, nil
}

// reselect keeps the cursor on the same pipeline across refreshes.
// Match on a real ID instead of Name if the API provides one.
func reselect(old []row, cursor int, fresh []row) int {
	if cursor < len(old) {
		for i, r := range fresh {
			if r.Name == old[cursor].Name {
				return i
			}
		}
	}
	return max(min(cursor, len(fresh)-1), 0)
}

func (m model) View() tea.View {
	v := tea.NewView(m.render())
	v.AltScreen = true
	return v
}

func (m model) render() string {
	switch {
	case m.width == 0:
		return "loading…"
	case m.width < minWidth || m.height < minHeight:
		return fmt.Sprintf("terminal too small: need %dx%d\nresize, or press q to quit", minWidth, minHeight)
	case m.detail:
		// For Detail longer than the screen, put this in a bubbles/viewport.
		r := m.rows[m.cursor]
		body := lipgloss.NewStyle().Width(m.width).Render(clean(r.Detail, true))
		return fit(clean(r.Name, false), m.width) + "\n\n" + body + "\n\n" +
			mutedStyle.Render(fit("esc back · q quit", m.width))
	}

	var b strings.Builder
	b.WriteString(m.status() + "\n")
	visible := m.height - 2
	nameW := min(20, m.width/3)
	start := max(0, m.cursor-visible+1)
	for i := start; i < min(len(m.rows), start+visible); i++ {
		r := m.rows[i]
		line := fit(clean(r.Name, false), nameW) + "  " + fit(clean(r.Detail, false), m.width-nameW-2)
		if i == m.cursor {
			line = selStyle.Render(line)
		}
		b.WriteString(line + "\n")
	}
	b.WriteString(mutedStyle.Render(fit("↑/↓ move · enter detail · r refresh · q quit", m.width)))
	return b.String()
}

func (m model) status() string {
	switch {
	case m.err != nil && len(m.rows) == 0:
		return errStyle.Render(fit("✗ couldn't load pipelines: "+m.err.Error()+" · r retry", m.width))
	case m.err != nil:
		return errStyle.Render(fit(fmt.Sprintf("✗ refresh failed, showing data from %s: %v · r retry",
			m.updated.Format("15:04:05"), m.err), m.width))
	case m.loading:
		return fit("Pipelines · loading…", m.width) // old rows stay visible below
	case len(m.rows) == 0:
		return fit("No pipelines returned by the CI API · r refresh", m.width)
	}
	return mutedStyle.Render(fit(fmt.Sprintf("Pipelines · %d · updated %s",
		len(m.rows), m.updated.Format("15:04:05")), m.width))
}

// fit truncates or pads s to exactly w terminal cells.
func fit(s string, w int) string {
	s = ansi.Truncate(s, w, "…")
	return s + strings.Repeat(" ", max(0, w-ansi.StringWidth(s)))
}

// clean strips escape sequences and control characters from API text.
// keepLines preserves newlines for the wrapped detail view.
func clean(s string, keepLines bool) string {
	return strings.Map(func(r rune) rune {
		switch {
		case r == '\n' && keepLines:
			return r
		case r == '\n' || r == '\r' || r == '\t':
			return ' '
		case unicode.IsControl(r):
			return -1
		}
		return r
	}, ansi.Strip(s))
}
```

Start it with `tea.NewProgram(newModel()).Run()`. If you stay on v1, use `tea.KeyMsg`, `View() string`, and `tea.WithAltScreen()`; the rest is the same. I haven't compiled this, since `row` and the imports weren't in the snippet.

## Tests to add before merging

1. **`Update` unit tests:** send `rowsMsg{err: …}` with and without existing rows, and check that old rows are kept and `err` is set. Send `rowsMsg{rows: reordered}` and check that the cursor follows the pipeline by name. Press `r` while loading and check that no command comes back.
2. **Unit test for `clean`:** input with `\x1b]52;…`, `\x1b[2J`, and newlines.
3. **Golden screenshots:** use `teatest/v2` with `tea.WithColorProfile(colorprofile.ASCII)` at 80×24, 60×24, and 39×24 (the too-small state). Include CJK names and a `Detail` of more than 500 characters.
