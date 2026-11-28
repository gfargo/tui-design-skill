I've read the skill's Go and layout guidance; here's the review.

# Review: CI pipelines Bubble Tea model

**Verdict: don't merge yet.** Two problems will hurt users right away. Pressing `r` freezes the whole UI, and in some cases you can't even quit. And API text is drawn straight to the terminal. Below are the problems from most to least harmful, each with a fix.

## 1. Pressing `r` blocks `Update` with a network call that never times out

`http.Get` runs inside `Update`, on the event loop, and `http.DefaultClient` has no timeout. While the request is open the screen doesn't redraw and no keys are handled, including `q` and `Ctrl+C`. If the CI API stops responding, people have to kill the tmux pane.

There are three related bugs in the same block:
- **A failed decode still counts as success.** The error from `Decode` is ignored, so a 500 error page or a schema change sets `ok = true`.
- **The status code is never checked.** A 401 or 503 response looks like a successful fetch.
- **Bad data can wipe good data.** Decoding goes straight into `m.rows`, so a half-parsed response replaces the last good list.

**Fix:** move the fetch into a `tea.Cmd` with a timeout, decode into a local variable, and send the result back as a message.

```go
type pipelinesMsg struct {
	rows []row
	at   time.Time
}
type fetchErrMsg struct{ err error }

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
		return fetchErrMsg{fmt.Errorf("decoding response: %w", err)}
	}
	return pipelinesMsg{rows: rows, at: time.Now()}
}

// In Update
case "r":
	if m.loading {
		return m, nil // don't stack requests
	}
	m.loading = true
	return m, fetchPipelines

case pipelinesMsg:
	m.loading, m.err = false, nil
	m.rows, m.updated = msg.rows, msg.at
	m.cursor = min(m.cursor, max(len(m.rows)-1, 0))
case fetchErrMsg:
	m.loading, m.err = false, msg.err // keep the last good rows on screen
```

Also return `fetchPipelines` from `Init` (and start the model with `loading: true`). Right now the first screen is empty until someone presses `r`.

## 2. API text is printed to the terminal unfiltered

`Name` and `Detail` come from the CI API, and `Detail` is free text: commit messages, error output, log lines. Any escape sequence in it reaches the terminal as a command. It can recolor or clear the screen, move the cursor, or set the window title. Newlines and tabs also break the one-line-per-row layout.

**Fix:** clean every string from the API before you measure or render it:

```go
func clean(s string) string {
	return strings.Map(func(r rune) rune {
		switch {
		case r == '\n' || r == '\t' || r == '\r':
			return ' '
		case r < 0x20 || r == 0x7f || (r >= 0x80 && r < 0xa0):
			return -1 // drop ESC and other control characters
		}
		return r
	}, s)
}
```

## 3. The hard-coded width breaks in small panes, and long `Detail` makes it worse

- **The window size is ignored.** `const width = 80` and there's no `tea.WindowSizeMsg` case. In a 60-column pane the 80-dash rule doesn't fit. Long `Detail` lines either wrap onto several lines, so one pipeline no longer equals one line, or get cut off with no ellipsis, depending on the renderer.
- **Height is ignored too.** Every row is printed. When there are more pipelines than the pane has lines, rows fall off the screen and the status dot can go with them.
- **Padding is counted in runes, not screen cells.** `%-20s` doesn't measure display width, so CJK or emoji in a name throws the columns out of line. Names longer than 20 characters are never cut, so they push `Detail` along.

**Fix:** store the size, work out column widths from it, and truncate by display width with an ellipsis. Cut prose like `Detail` at the end so the start stays readable.

```go
case tea.WindowSizeMsg:
	m.width, m.height = msg.Width, msg.Height

// View helper: one table cell, cut to w display cells
func cell(s string, w int) string {
	s = ansi.Truncate(clean(s), w, "…") // github.com/charmbracelet/x/ansi
	return s + strings.Repeat(" ", max(w-lipgloss.Width(s), 0))
}

nameW := min(20, m.width/3)
detailW := m.width - nameW - 2 // 2-cell gap between columns
```

Only render the rows that fit in `m.height - 2`, scrolled so the cursor stays visible. A simpler route is `bubbles/table`, which already handles width-aware truncation, scrolling and the cursor.

## 4. `cursor` is never used, so the full `Detail` can't be read

The model has a `cursor` field, but no key moves it and nothing draws it. Once `Detail` is truncated (and it has to be), users have no way to read the rest.

**Fix:**
- Bind `↑`/`k` and `↓`/`j` to move the cursor, and keep it within the number of rows.
- Show the selected row in reverse video. Use that alone, with no extra marker.
- Make `Enter` open a `bubbles/viewport` that shows the full, wrapped `Detail` for that row, and `Esc` go back to the list.

This also makes small panes work: the table shows a short preview and the full text is one key away.

## 5. The status dot misleads and only uses color

- **It's red before anything has happened.** `ok` starts as `false`, so the app shows "failed" before any fetch has run.
- **It has two values but there are more states.** Loading, empty, error-with-old-data and success all look the same. The actual error message is thrown away.
- **Color is the only signal.** The `●` looks the same in both states. Users with red-green color blindness, and anyone using `NO_COLOR` or a monochrome terminal, can't tell pass from fail.
- **`●` can be one or two cells wide.** It's an "ambiguous width" character, so it can knock alignment off on terminals set to treat those as wide.
- **Colors are hard-coded.** `"1"`/`"2"` are raw numbers scattered in `View`. Define named styles (error, muted, and so on) once.

**Fix:** replace `ok` with `loading`, `err` and `updated`, and show a status line that uses a word or symbol plus color:

```
loading…
✗ refresh failed: HTTP 503 Service Unavailable · showing data from 14:02 · r retry
No pipelines returned. r refresh
✓ updated 14:05:12
```

## 6. The keys are hidden and there's no alternate screen

- **Users can't discover the keys.** Nothing tells a first-time user that `r` exists. Add a short footer: `↑↓ move · enter detail · r refresh · q quit`. It can share the status line when space is tight.
- **It should use the alternate screen.** A full-screen list with a cursor in a tmux pane should take over the pane while it runs, rather than drawing inline. In your v1 code that's `tea.NewProgram(m, tea.WithAltScreen())`.

## 7. Version note

`tea.KeyMsg` and `View() string` are the Bubble Tea v1 API. v2 has been stable since February 2026. If this is new code, consider moving now:

| v1 (your code) | v2 |
|---|---|
| `tea.KeyMsg` | `tea.KeyPressMsg` |
| `View() string` | `View() tea.View` |
| alt screen as a program option | `v.AltScreen = true` |
| — | color-profile handling that honors `NO_COLOR` |

The fixes above apply to either version. Also, the snippet has no imports and no `row` type, so I'm assuming those were cut for the paste.

## Clutter check

- **Borders:** none. That's good.
- **The dashed rule:** 80 cells of pure decoration that don't fit at 60 columns. Replace it with a dim header row (`Pipeline  Detail`) that tells the reader something.
- **Signals for one state:** the dot and its color carry pass/fail, but the shape never changes. In effect that's color alone (see §5).
- **Markers on every row:** none. Keep it that way, and mark only the selected row.
- **Minor:** `s +=` in a loop allocates a new string per row. Use a `strings.Builder`.

## What happens at 80×24 and 60 columns after the fixes

```
80 columns                                                                 
Pipeline              Detail                                               
deploy-api            Rolling back release 4.2.1 after health check fai…   
build-web             ✓ 3m12s on main @ a1b2c3d                            
lint                  Waiting for runner                                   
                                                                           
✓ updated 14:05:12        ↑↓ move · enter detail · r refresh · q quit      

60 columns                                     
Pipeline            Detail                     
deploy-api          Rolling back release 4.2…  
build-web           ✓ 3m12s on main @ a1b2c3d  
✓ 14:05:12   ↑↓ · enter detail · r · q          
```

- **At 80×24:** the full table, with `Detail` cut at the end.
- **At 60 columns:** the name column shrinks to `width/3` and `Detail` gets the rest. The footer shortens, but `?` or the help line still lists every key.
- **Below about 40×6:** don't draw a broken frame. Show `terminal too small: need 40x6, resize or press q to quit`, and keep `q` and `Ctrl+C` working.

## Tests to add before merging

1. **`Update` unit tests:**
   - an error message keeps the old rows and sets `err`;
   - a success message clears `err`;
   - `r` while loading doesn't start a second fetch;
   - the cursor stays in range after the row list shrinks.
2. **Fetch tests against `httptest.Server`:** a non-200 response, bad JSON, and a timeout.
3. **Golden-file tests of `View`:** at 80×24, 60×24 and the minimum size, with the color profile pinned. Use a `Detail` with CJK text, an escape sequence and a 500-character line.

Of all this, §1 and §2 have to be fixed before merging. §3–§5 are what make it usable in small tmux panes.
