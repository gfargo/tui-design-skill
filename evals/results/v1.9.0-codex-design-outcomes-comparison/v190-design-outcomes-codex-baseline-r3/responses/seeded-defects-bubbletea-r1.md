I’d fix three things before merging: the refresh blocks the UI, failed responses can look successful, and rendering is unbounded.

1. **The HTTP request blocks Bubble Tea’s event loop.**  
   `Update` must return quickly. While `http.Get` or decoding waits, the app cannot process keys, resize messages, or quit.

   Move the request into a `tea.Cmd` that returns a result message. Handle that message in `Update` to change the model. Use an HTTP client with a timeout and, ideally, request cancellation.

2. **Errors are ignored and HTTP failures count as success.**  
   `http.Get` returns no error for HTTP 404 or 500. The decoder error is discarded, so malformed JSON can still set `ok = true`. Decoding directly into `m.rows` can also leave partially decoded data behind.

   Check the status code, limit the response body size, decode into a temporary slice, and return either validated rows or an error. Replace `m.rows` only after successful decoding; preserve the previous data on failure. Closing the body is already handled correctly.

3. **The layout will break in small panes.**  
   A fixed 80-column divider can wrap. `%-20s` specifies a *minimum* width, so long names expand the column. Long details wrap unpredictably, and rendering every row can push the status below the visible area.

   Handle `tea.WindowSizeMsg` and store the current width and height. Allocate column widths from the available space, then explicitly wrap or truncate details. Render only the rows that fit, using pagination or a viewport, and reserve space for status/help. Handle widths smaller than the normal column layout explicitly.

4. **API text needs terminal-safe rendering.**  
   Names and free-text details can contain newlines, tabs, control characters, or terminal escape sequences. These can disrupt the layout or manipulate terminal output.

   Sanitize untrusted text before rendering. Remove terminal escapes and unwanted control characters; normalize whitespace according to whether details should be single-line or multiline. Use terminal display-width-aware utilities for padding and truncation so emoji, combining marks, and wide characters behave correctly.

5. **A boolean cannot describe the refresh state clearly.**  
   Initially, `ok == false` displays a red dot even though no request has failed. There is no loading state or explanation of an error, and color alone is ambiguous.

   Track idle/loading/success/error explicitly, with an error field and a text label such as `Refreshing…` or `Refresh failed: timeout`. If retaining old rows after failure, make their stale status clear.

6. **Async refresh needs an overlap policy.**  
   Once fetching moves into commands, repeated `r` presses can create concurrent requests whose results arrive out of order.

   Either ignore refresh while loading, cancel the previous request, or attach request IDs and discard stale results.

The core structure should look like this:

```go
case tea.KeyMsg:
	switch msg.String() {
	case "q", "ctrl+c":
		return m, tea.Quit
	case "r":
		if m.loading {
			return m, nil
		}
		m.loading = true
		m.err = nil
		return m, fetchRowsCmd()
	}

case rowsResultMsg:
	m.loading = false
	m.err = msg.err
	if msg.err == nil {
		m.rows = msg.rows
		// Clamp cursor and scroll position to the new rows.
	}

case tea.WindowSizeMsg:
	m.width, m.height = msg.Width, msg.Height
	// Recompute layout and viewport dimensions.
```

`fetchRowsCmd` should return data rather than mutate the model. Also, `cursor` currently does nothing: remove it if selection is unnecessary, or implement navigation and keep it valid after refreshes.

Before merging, I’d verify a slow request still allows quitting, failed/malformed responses preserve existing rows, and narrow panes handle long Unicode text and embedded control characters cleanly.