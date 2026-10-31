I've read the skill's Bubble Tea and layout references, and the review is below, ordered from most to least harmful to users.

# Review: CI pipelines model

**Verdict: don't merge yet.** Two problems block the merge. The UI freezes during every refresh, and the layout breaks in exactly the small tmux panes people use it in. Several smaller issues follow from those two.

## Blocking

### 1. The network call runs inside `Update`, so the UI freezes
`http.Get` runs on Bubble Tea's event loop. While it waits, the app doesn't redraw or handle keys, including `q` and `Ctrl+C`. `http.Get` uses `http.DefaultClient`, which has **no timeout**. If the CI API stalls, the app hangs until someone kills the tmux pane.

**Fix:** move the request into a `tea.Cmd` with a timeout and send the result back as a message. Don't start a second fetch while one is running (see the code below).

### 2. Fetch errors are ignored and "ok" can be wrong
- The error from `Decode` is thrown away and `m.ok = true` is set anyway. A truncated or changed JSON response shows a green dot.
- A non-2xx response (a 502 HTML page, a 401) never counts as a failure. It only shows up as a decode error, which is ignored.
- Decoding straight into `m.rows` means a failed decode can leave partial data in place.
- When a request fails, the error text is dropped. The user just sees a red dot with no reason and no next step.

**Fix:** check the status code, decode into a local slice, and only replace `m.rows` on success. Store the error itself (`err error`), not a bool. On failure, keep the last good rows on screen and label them stale.

### 3. The fixed width of 80 breaks in small panes
The model never handles `tea.WindowSizeMsg`. What a 60-column tmux split shows:

```
--------------------------------------------------------   ← 80-dash rule wraps
------------------------                                     onto a second line
build-and-test       Step "integration" failed after 3 re   ← long Detail wraps the
tries: connection reset by peer while pulling image ghcr.      terminal line, so one
io/example/app:sha-41ac…                                       row takes 2–4 lines
●                                                            ← red/green, nothing else
```

It also never limits height. With 40 pipelines in a 24-row pane, the top rows scroll off and the cursor can't reach them.

**Fix:** store width and height from `WindowSizeMsg`. Calculate column widths from them, **truncate each cell to fit and never wrap**, and show only as many rows as the pane can hold. Below a minimum size, show a "terminal too small" message instead of a broken screen.

### 4. `Detail` is untrusted text written straight to the terminal
The text comes from a CI API, so it's free text you don't control. It can contain:
- newlines and tabs, which break the one-row-per-pipeline layout;
- ANSI escape sequences, which are common in CI logs. Something like `\x1b[2J` would clear the screen, and other sequences can retitle the window or emit hyperlinks. Bubble Tea passes them through as-is.

**Fix:** clean the text once when it arrives. Remove escape sequences, then replace control characters with spaces. Keep the full text for a detail view.

## High

### 5. Columns are measured in bytes, not screen cells
`%-20s` pads by byte count. A name with CJK characters, accents or emoji throws the Detail column off on that row. Names longer than 20 characters aren't cut short either; they push Detail to the right. Use `ansi.StringWidth`, `ansi.Truncate` or `lipgloss.Width` instead.

### 6. Status is shown by color alone, and the starting state is "error"
- A red or green `●` means nothing to colorblind users, under `NO_COLOR`, or in a monochrome theme.
- `●` has ambiguous width, so it can take two cells in some terminal setups.
- Because `ok` starts as `false`, a fresh launch shows **red** before anything has failed.
- A bool can't express all the states the app needs: initial, loading, ok, empty, error-with-stale-data.

**Fix:** use a status line that starts with a symbol or word, with color as a second cue:

```
✓ updated 14:02:31
✗ refresh failed: HTTP 502 Bad Gateway · showing data from 14:02:31 · r retry
No pipelines returned. r refresh
```

Define named styles once (`styleOK`, `styleErr`, `styleSelected`) instead of writing `lipgloss.Color("1")` inside `View`.

### 7. Nothing happens on launch and nothing tells you what to press
`Init` returns `nil`, so the app opens to a dashed line and a red dot until someone guesses that `r` refreshes. **Fix:** fetch from `Init` and add a footer: `↑/↓ move ⋅ r refresh ⋅ q quit`.

### 8. `cursor` is never used
There's no navigation, no visible selection, and no way to read a long `Detail`. When you add these:
- Show the selected row in reverse video.
- Let Enter open the full detail in a `viewport`.
- Track the selection by **pipeline ID**, not by row index, so a refresh doesn't move it under the user.

## Medium

- **Alt screen.** This is a full-screen dashboard of variable height, so run it with `tea.WithAltScreen()`. That's for v1; in v2 you set `v.AltScreen = true` in `View`.
- **Bubble Tea version.** `View() string` and `tea.KeyMsg` are the v1 API. Bubble Tea v2 is the current stable release. If this is new code, consider moving to v2 now (`View() tea.View`, `tea.KeyPressMsg`) rather than after the merge. Everything else in this review applies to both.
- **`View` builds the frame with `s +=`.** Use a `strings.Builder` and only render the visible rows. If the pipeline list gets long, use `bubbles/table` or `list`, which only render what's visible.

## Clutter and minimum size

**Clutter:**
- There are no borders, which is good.
- The 80-dash rule is the only chrome. It carries no information and takes two lines at 60 columns. Replace it with the status line.
- Pipeline status uses one signal (color). It needs two: color plus a symbol or word.
- No marker appears on every row.

**What happens at each size with the fix below:**

| Size | Behavior |
|---|---|
| 80×24 | Status line, 22 pipeline rows, footer. Name column 20 cells, Detail cut to 58 cells. |
| 60 columns | Same layout. Detail cut to 38 cells. Enter shows the full text. |
| Below 40×5 | `terminal too small: need 40x5 · q quit`. `q` and `Ctrl+C` still work. |

## Suggested fix (v1 API, to match your code)

```go
const (
	pipelinesURL = "https://ci.example.com/api/pipelines"
	minWidth     = 40
	minHeight    = 5
)

var (
	styleOK       = lipgloss.NewStyle().Foreground(lipgloss.Color("2"))
	styleErr      = lipgloss.NewStyle().Foreground(lipgloss.Color("1"))
	styleMuted    = lipgloss.NewStyle().Faint(true)
	styleSelected = lipgloss.NewStyle().Reverse(true)
)

type pipelinesMsg struct{ rows []row }
type fetchErrMsg struct{ err error }

type model struct {
	rows          []row
	cursor        int
	width, height int
	loading       bool
	err           error
	fetchedAt     time.Time
}

func newModel() model { return model{loading: true} }

func (m model) Init() tea.Cmd { return fetchPipelines }

func fetchPipelines() tea.Msg {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, pipelinesURL, nil)
	if err != nil {
		return fetchErrMsg{err}
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fetchErrMsg{err}
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fetchErrMsg{fmt.Errorf("HTTP %s", resp.Status)}
	}
	var rows []row
	if err := json.NewDecoder(resp.Body).Decode(&rows); err != nil {
		return fetchErrMsg{fmt.Errorf("bad response: %w", err)}
	}
	for i := range rows {
		rows[i].Name, rows[i].Detail = clean(rows[i].Name), clean(rows[i].Detail)
	}
	return pipelinesMsg{rows}
}

// clean makes API text safe to put in a single table cell.
func clean(s string) string {
	return strings.Map(func(r rune) rune {
		if unicode.IsControl(r) {
			return ' '
		}
		return r
	}, ansi.Strip(s))
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "r":
			if m.loading {
				return m, nil
			}
			m.loading = true
			return m, fetchPipelines
		case "up", "k":
			m.cursor = max(m.cursor-1, 0)
		case "down", "j":
			m.cursor = min(m.cursor+1, max(len(m.rows)-1, 0))
		}
	case pipelinesMsg:
		// TODO: re-find the selection by pipeline ID instead of clamping the index.
		m.rows, m.err, m.loading, m.fetchedAt = msg.rows, nil, false, time.Now()
		m.cursor = min(m.cursor, max(len(m.rows)-1, 0))
	case fetchErrMsg:
		m.err, m.loading = msg.err, false // keep m.rows: last known good
	}
	return m, nil
}

func (m model) View() string {
	if m.width == 0 {
		return "loading pipelines…"
	}
	if m.width < minWidth || m.height < minHeight {
		return fmt.Sprintf("terminal too small: need %dx%d\nq quit", minWidth, minHeight)
	}

	var b strings.Builder
	b.WriteString(ansi.Truncate(m.statusLine(), m.width, "…") + "\n")

	nameW := min(20, m.width/3)
	detailW := m.width - nameW - 2
	bodyH := m.height - 2 // status line + footer
	start := max(0, m.cursor-bodyH+1)
	end := min(len(m.rows), start+bodyH)
	for i := start; i < end; i++ {
		r := m.rows[i]
		line := cell(r.Name, nameW) + "  " + cell(r.Detail, detailW)
		if i == m.cursor {
			line = styleSelected.Render(line)
		}
		b.WriteString(line + "\n")
	}
	for i := end - start; i < bodyH; i++ {
		b.WriteString("\n")
	}
	b.WriteString(styleMuted.Render(ansi.Truncate("↑/↓ move ⋅ r refresh ⋅ q quit", m.width, "…")))
	return b.String()
}

// cell truncates s to w terminal cells and pads it to exactly w.
func cell(s string, w int) string {
	s = ansi.Truncate(s, w, "…")
	return s + strings.Repeat(" ", w-ansi.StringWidth(s))
}

func (m model) statusLine() string {
	switch {
	case m.err != nil && len(m.rows) > 0:
		return styleErr.Render(fmt.Sprintf("✗ refresh failed: %v · showing data from %s · r retry",
			m.err, m.fetchedAt.Format("15:04:05")))
	case m.err != nil:
		return styleErr.Render(fmt.Sprintf("✗ cannot load pipelines: %v · r retry", m.err))
	case m.loading:
		return "loading pipelines…"
	case len(m.rows) == 0:
		return "No pipelines returned by ci.example.com · r refresh"
	default:
		return styleOK.Render("✓ updated " + m.fetchedAt.Format("15:04:05"))
	}
}
```

Notes on the fix:
- `ansi` is `github.com/charmbracelet/x/ansi`, which Lipgloss already depends on.
- Text is cleaned once when the response arrives, not on every frame.
- During a refresh the status line says "loading…" and the old rows stay visible.
- Still to do: Enter opens a `viewport` with the full `Detail`, and the selection follows the pipeline ID across refreshes.

## Tests to add before merging

1. **`Update` tests:**
   - `r` while loading returns no command.
   - `fetchErrMsg` keeps the existing rows.
   - `WindowSizeMsg{60, 24}` followed by `View()` gives no line wider than 60 cells (check with `lipgloss.Width`) and no more than 24 lines.
2. **`fetchPipelines` against `httptest.Server`:** cover a 200 response, a 502 with an HTML body, a truncated JSON body, and a slow handler that should hit the timeout.
3. **Golden screen snapshots** at 80×24, 60×24 and 39×10 (too small), with the color profile pinned. Use fixture rows that include CJK text, emoji, an embedded `\n`, and `\x1b[2J`.
