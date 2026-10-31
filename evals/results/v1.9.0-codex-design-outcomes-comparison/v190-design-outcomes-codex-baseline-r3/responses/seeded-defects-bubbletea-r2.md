I’d fix these issues before merging, especially the blocking request and unbounded rendering.

1. **The HTTP request blocks the UI.**  
   `Update` runs on Bubble Tea’s event loop. While `http.Get` waits, the app cannot process keys, resize events, or quit normally.

   **Fix:** return a `tea.Cmd` that fetches the rows and sends a result message. Apply that message in `Update`:

   ```go
   type rowsMsg struct {
       rows []row
       err  error
   }

   // In the key handler:
   case "r":
       if m.loading {
           return m, nil
       }
       m.loading = true
       return m, fetchRowsCmd(m.client)
   ```

   Handle `rowsMsg` by clearing `loading`, recording the error, and replacing rows only on success. If you allow overlapping refreshes, attach request IDs so an older response cannot overwrite newer data.

2. **Failures can be reported as success, and decoding can damage existing data.**  
   `http.Get` does not treat HTTP 4xx/5xx as errors. The decoder’s error is ignored, and decoding directly into `m.rows` can leave partially decoded data. `ok` becomes true regardless.

   **Fix:** check the HTTP status, decode into a temporary slice, and return errors through `rowsMsg`. Preserve the last successful rows when refreshing fails. For an API boundary, also impose a reasonable response-size limit.

3. **The request has no timeout.**  
   The default HTTP client has no overall request timeout. Moving the request into a command keeps the UI responsive, but the request can still remain outstanding indefinitely.

   **Fix:** use a reusable `http.Client` with a timeout, or a request context with a deadline. Keep closing the response body as the current code does.

4. **The layout ignores the terminal size.**  
   A fixed 80-column separator and every row rendered at once will overflow small tmux panes. `%-20s` specifies a *minimum* width; long names are never truncated.

   **Fix:** store width and height from `tea.WindowSizeMsg`. Allocate a bounded name column and give the remaining space to detail. Reserve lines for status/help, and render only the rows or wrapped content that fit. Clamp all calculated dimensions to zero or greater.

5. **Long details need an explicit overflow policy.**  
   A single detail can wrap across many terminal lines, pushing other rows and the status off-screen. Embedded newlines also break the assumed one-row-per-line layout.

   **Fix:** for the list, normalize line breaks and truncate details to the available display width. Show full details in a separate scrollable viewport when selected. If you prefer wrapping in the list, navigation and scrolling must account for each row’s rendered height.

6. **API text should be treated as untrusted terminal content.**  
   Names and details can contain escape sequences, carriage returns, tabs, and other control characters that alter the display or terminal state.

   **Fix:** sanitize API text before rendering: remove terminal escape sequences and unwanted control characters, and normalize whitespace according to the layout. Use terminal-cell-aware truncation and measurement, such as the appropriate Lip Gloss/ANSI helpers for your version. Byte counts and rune counts do not reliably measure emoji or wide characters.

7. **The status indicator is ambiguous and relies entirely on color.**  
   The initial `ok == false` displays a red dot before any request has failed. There is no loading state or error explanation, and color alone is insufficient when color is unavailable or hard to distinguish.

   **Fix:** represent idle, loading, success, and error explicitly. Render text such as “Refreshing…” or “Refresh failed: …”, with color as an additional cue. Sanitize and bound error text too.

8. **`cursor` is unused, and selection can become invalid after refresh.**  
   There is currently no navigation or selected-row rendering.

   **Fix:** either remove it or implement navigation and scrolling. After refresh, preserve selection by a stable pipeline ID where possible; otherwise clamp the cursor to the new row count and handle an empty list without indexing it.

For verification, I’d cover failed HTTP statuses, malformed JSON, refresh failure preserving existing rows, empty results, and a refresh that removes the selected row. I’d also inspect rendering in a very narrow and short pane with long names, multiline details, wide Unicode, and embedded terminal escapes.