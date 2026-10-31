I would hold the merge. The main blockers are blocking network I/O, reporting failed responses as successful, and rendering unbounded API text into a fixed-width screen.

This uses **Bubble Tea v1-style APIs** (`tea.KeyMsg`, `View() string`). The fixes below fit that architecture; a v2 migration is a separate change.

1. **Refresh freezes the UI, including quit and resize.**  
   `http.Get` and JSON decoding run inside `Update`. The default HTTP client has no overall timeout, so a slow CI API can leave the interface stuck indefinitely.

   **Fix:** return a `tea.Cmd` that fetches and decodes into a local slice, then returns a typed result message. Apply that result in `Update`. Use a reusable HTTP client with a timeout and request cancellation. Keep commands from mutating the model.

   ```go
   type rowsLoadedMsg struct {
       rows []row
       err  error
   }

   // Update:
   case rowsLoadedMsg:
       m.loading = false
       m.err = msg.err
       if msg.err == nil {
           m.rows = msg.rows
       }
   ```

   While loading, either ignore repeated `r` presses or cancel the previous request. If overlapping requests are allowed, use request IDs so an older response cannot overwrite newer data.

2. **HTTP and decoding failures appear green.**  
   `http.Get` does not treat HTTP 401 or 500 as errors. The decode error is discarded, and `m.ok = true` executes regardless. Decoding directly into `m.rows` can also leave partially modified data after a decoding error.

   **Fix:** check the expected HTTP status, check decoding errors, and replace rows only after the entire response passes validation. Bound the response size and report an oversized response explicitly. Keep the last successful rows on refresh failure and label them stale. Closing the response body is already handled correctly.

3. **API text can break the layout and inject terminal controls.**  
   Both fields are rendered verbatim. `Detail` can contain newlines, tabs, carriage returns, or escape sequences that alter the screen, cursor, or terminal state. A long `Name` also overflows: `%-20s` sets a **minimum** width, not a maximum.

   **Fix:** treat API strings as untrusted display data. Remove terminal escape sequences and disallowed controls with a tested sanitizer. Convert newlines and tabs to spaces for table summaries; preserve safe newlines in the detail view. Sanitize before measuring and truncating, then apply your own styles.

4. **Width handling fails in tmux and with Unicode.**  
   The 80-character separator wraps in a 60-column split. `fmt` padding does not measure terminal cells, so CJK characters, combining marks, and emoji misalign columns.

   **Fix:** store width and height from `tea.WindowSizeMsg`. Calculate column budgets from the available cells, including selection markers and separators. Use terminal-cell measurement such as `lipgloss.Width` and a grapheme-aware truncator such as `ansi.Truncate`. Truncate each table field explicitly; setting a style width alone may wrap it.

5. **The list has no height limit or usable navigation.**  
   Every row and every detail is rendered. Large responses make frames expensive, push status off-screen, and leave rows unreachable. `cursor` currently does nothing.

   **Fix:** reserve space for header and footer, then render only the visible row range. Add Up/Down, Page Up/Page Down, Home/End, and a visible selection marker. `Enter` should open the full detail in a scrollable, wrapped viewport; `Esc` returns to the list. Preserve selection across refresh by stable pipeline ID, with a neighboring-row fallback if it disappears.

6. **The status is ambiguous and inaccessible.**  
   Initial state looks like an error because `ok` defaults to false. A successful empty response looks like a nearly blank screen. The dot relies entirely on red versus green, and could be mistaken for pipeline health rather than fetch status.

   **Fix:** represent initial/loading/loaded/error states explicitly, alongside `err` and the last successful refresh time. Show text such as `Loading pipelines...`, `No pipelines found`, or `Refresh failed; showing stale data — r retry`. Use semantic color styles as reinforcement, honor `NO_COLOR`, and keep an ASCII presentation available. Start the first fetch from `Init`, unless manual loading is intentional and visibly explained.

I’d use a single list with detail drill-down for this workflow. It suits small panes without requiring a persistent preview panel.

```text
80-column pane                         60-column pane
Pipelines — Updated 12:03               Pipelines — Updated 12:03
  NAME                 DETAIL            NAME            DETAIL
> deploy-api           Waiting for...  > deploy-api      Waiting for...
  unit-tests           Running...        unit-tests      Running...
...
1/128  Up/Down move  Enter detail       1/128  Up/Down move  Enter detail
r refresh  q quit                      r refresh  q quit
```

At **80×24**, reserve four lines for header, column labels, and controls, leaving 20 data rows. At **60 columns**, shrink the name column and truncate summaries; full details remain reachable through Enter. Below 60, hide the summary column and show names only. A reasonable proposed hard minimum is **30×6**; below that, render a bounded “Terminal too small; need 30×6” message while keeping quit working. Clamp all size calculations to avoid negative dimensions.

The clutter audit is small but concrete: border nesting is zero; there are no repeated row markers; the only status signal is color. Remove the decorative 80-dash line—it consumes 80 cells and a full row, about 4.2% of a 24-line pane—and replace the isolated dot with meaningful status text. Don’t add per-row bullets beyond the selected-row marker.

Before merging, I’d verify:

- Fetch success, HTTP errors, malformed JSON, timeout, empty results, and failed refresh preserving old rows.
- Quit and resize remain responsive during a delayed request.
- Frames fit at 80×24, 60 columns, and below the minimum, including long names, multiline details, Unicode, and hostile control sequences.
- Scrolling and selection survive refresh, reorder, and row deletion.
- Monochrome status remains understandable.

The program setup isn’t shown, so terminal cleanup cannot be assessed here. For this browsing session, use v1’s framework-managed alternate screen and normal `Run`/`tea.Quit` lifecycle; keep diagnostics out of the active screen. Also provide linear output for non-TTY and accessibility use.