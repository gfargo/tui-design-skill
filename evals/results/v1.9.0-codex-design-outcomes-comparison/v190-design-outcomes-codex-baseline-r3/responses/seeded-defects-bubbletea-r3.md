I’d fix three merge blockers: HTTP work blocks the UI, failed responses can appear successful, and rendering doesn’t respect the terminal’s dimensions.

1. **The HTTP request blocks Bubble Tea’s event loop.**  
   `Update` runs synchronously, so a slow API freezes input and redraws—including handling `q`. `http.Get` also has no overall timeout.

   **Fix:** Return a `tea.Cmd` that fetches and decodes the data, then returns a result message. Use an HTTP client with a timeout. Track `loading` and either ignore repeated refreshes while loading or use request IDs to prevent older responses from overwriting newer data. `Init` can return the same command if initial loading is intended.

   ```go
   type rowsLoadedMsg struct {
       rows []row
       err  error
   }
   ```

   The command performs I/O; `Update` handles this message and changes model state.

2. **HTTP and decoding failures are reported as success.**  
   `http.Get` doesn’t treat HTTP 4xx/5xx responses as errors, and the JSON decoding error is discarded. Decoding directly into `m.rows` can also leave partially decoded data when decoding fails.

   **Fix:** Check for a successful status, decode into a temporary slice, and replace `m.rows` only after validation succeeds. Apply a sensible response-size limit. On failure, preserve the last successful rows and expose the error.

3. **The layout breaks in small panes and after resizing.**  
   `width = 80` ignores the actual terminal width. There’s also no height limit: enough rows or a long detail can push the status and useful content out of view.

   **Fix:** Handle `tea.WindowSizeMsg`, store width and height, and derive a content area after reserving space for status/help. Put the rows in a scrollable viewport. Recompute wrapping and viewport dimensions on resize, including very narrow or short sizes.

4. **`%-20s` doesn’t constrain the name column or wrap details.**  
   Twenty is a minimum padding width, so a long name pushes the detail column sideways. `fmt` padding also doesn’t reliably match terminal display widths for wide characters or combining characters.

   **Fix:** Use terminal-cell-aware measurement, truncation, and wrapping. Bound the name column, calculate the remaining detail width, and wrap `Detail` into that space. In narrow panes, switch to a stacked layout with the name above its detail. Clamp derived dimensions so they never become negative.

5. **API text is rendered as terminal content without sanitization.**  
   Names and free-text details may contain ANSI escape sequences, control characters, tabs, or embedded newlines that change the layout or terminal behavior.

   **Fix:** Sanitize external strings before rendering. Strip terminal escape sequences and unwanted controls, normalize tabs and line endings, and explicitly support intentional detail line breaks during wrapping.

6. **`ok` cannot describe the actual state, and the dot relies on color alone.**  
   Initially it shows red despite no request having failed. It cannot distinguish loading, empty results, refresh failure, or stale data. Red/green alone is also hard to interpret in some terminal themes and for some users.

   **Fix:** Track `loading`, `err`, and whether a successful load has occurred. Render text such as `Loading…`, `12 pipelines`, or `Refresh failed: … — showing previous results`, with color as an enhancement. Give long errors a bounded layout too.

7. **`cursor` is unused.**  
   There’s no navigation or selected-row rendering.

   **Fix:** Remove it if the screen only needs scrolling. If selection is intended, implement navigation and keep selection in bounds after refreshes; preferably preserve selection by a stable pipeline ID.

Before merging, I’d verify slow requests remain responsive, HTTP/decode failures preserve existing rows, and long Unicode/multiline details render correctly in a resized, very small pane. Also test empty results and API strings containing terminal escapes.