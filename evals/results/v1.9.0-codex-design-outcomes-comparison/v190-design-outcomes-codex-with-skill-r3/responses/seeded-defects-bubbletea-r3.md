I would hold the merge. The main problems are a blocking event loop, unreliable refresh results, and rendering that cannot fit small panes.

This uses Bubble Tea v1 APIs (`tea.KeyMsg`, `View() string`); the fixes below assume v1. A v2 migration is a separate change.

1. **The HTTP request freezes the UI.**  
   `http.Get` and decoding run inside `Update`, so a slow CI API prevents quitting, navigation, and resize handling. The default HTTP client has no overall timeout.

   **Fix:** return a `tea.Cmd` that fetches and decodes into a local slice, then returns a typed result message. Apply that result in `Update`. Use an injected HTTP client with a timeout and request cancellation; never have the command mutate `m.rows`.

2. **Failed responses can appear successful and damage existing data.**  
   `http.Get` does not treat HTTP 401 or 500 as errors. The decode error is ignored, and `m.ok = true` runs regardless. Decoding directly into `m.rows` can also leave partially changed data after failure.

   **Fix:** check the HTTP status, check decoding errors, and validate the expected payload before replacing rows. Preserve the last successful rows on failure and label them stale. Bound response size or use API pagination for large results.

   Once fetching is asynchronous, ignore repeated `r` presses while loading, or cancel the previous request and use request IDs to reject late results.

3. **API strings are rendered as terminal instructions and layout.**  
   Both fields are interpolated directly. Newlines, tabs, carriage returns, and escape sequences in CI data can break rows or manipulate terminal output.

   **Fix:** sanitize both fields before rendering. Strip terminal control sequences and unwanted control characters; flatten whitespace in table summaries. Preserve ordinary newlines only in the detail view. Sanitization and width truncation are separate steps.

4. **The layout has no width constraint.**  
   `width = 80` only sizes the separator. `%-20s` specifies a minimum field width, so a long name expands the column; `Detail` is unlimited. Go formatting also does not measure terminal display cells correctly for CJK, combining marks, or emoji.

   **Fix:** store dimensions from `tea.WindowSizeMsg`, calculate column budgets, and truncate sanitized values using terminal-cell-aware helpers such as `ansi.Truncate`. Measure with `lipgloss.Width`. Keep table rows on one line; show full detail in a wrapping, scrollable drill-down view.

5. **The layout has no height constraint or usable navigation.**  
   Every row is rendered, so large responses push content and status outside the pane. `cursor` is unused: users cannot select a row or inspect truncated detail.

   **Fix:** reserve space for status and controls, then render only the visible row range. Use a Bubbles list/table or maintain a cursor and scroll offset. Add arrows, page navigation, Enter for detail, and Esc to return. Preserve selection by stable CI row ID across refreshes; handle disappearing rows and empty lists safely.

6. **`ok` hides the actual state.**  
   Initial state looks like failure. Loading, empty results, connection failure, and malformed responses have no distinct presentation. The red/green dot conveys meaning only through color and does not say whether it describes the fetch or pipeline health.

   **Fix:** track loading, error, whether data has loaded, and last successful refresh time. Show explicit text:
   
   - `Loading pipelines...`
   - `Updated 14:32 · 28 pipelines`
   - `No pipelines returned · r refresh`
   - `Refresh failed: HTTP 503 · stale data · r retry`

   Keep fetch status separate from individual pipeline status. Define semantic styles, honor `NO_COLOR`, and retain all meaning without color.

7. **The controls are undiscoverable.**  
   Nothing tells a first-time user about `r` or `q`, and `Init` leaves the screen empty until they discover refresh.

   **Fix:** start the initial fetch through `Init`, with initial model state marked loading, and show a compact footer: `↑↓ move  Enter detail  r refresh  q quit`. Keep Ctrl+C working in every state. Add framework-managed Ctrl+Z suspension where supported.

For small panes, I would use a single list with detail on Enter. These sketches show the structure, with omitted rows:

```text
80×24                                  60-column tmux pane
Pipelines · updated 14:32               Pipelines · updated 14:32
NAME                 DETAIL            NAME           DETAIL
> deploy-production  Waiting for...    > deploy-prod... Waiting for...
  test-api           Integration...     test-api       Integration...
...
1/28                                   1/28
↑↓ move  Enter detail  r refresh q quit ↑↓ move Enter detail r refresh q quit
```

At 80×24, reserve three lines for status, column labels, and footer, leaving 21 list rows. At 60 columns, shrink the name budget and truncate both columns. In shorter panes, reduce visible rows. A reasonable proposed minimum is 40×6; below that, render a bounded “terminal too small: need 40×6” message while keeping quit and resize handling active.

The clutter audit is small: border depth is zero, there are no repeated row markers, and the separator consumes an entire line without identifying anything. Remove it. Replace the unexplained dot with labelled status, and use a selection marker only on the selected row.

The program startup code is absent, so terminal cleanup and screen mode cannot be verified here. For this persistent browsing workflow, use v1’s `tea.WithAltScreen()` and framework-managed cleanup. Provide linear text or JSON output for non-TTY use and accessibility.

Before merging, verify synthetic update transitions and pinned frames at 80×24, 60×12, the minimum, and below it. Cover slow requests with responsive quit/resize, HTTP and decode failures preserving old rows, empty and large results, selection after refresh, multiline/control-character input, Unicode widths, and monochrome output. A short PTY smoke test should check resize and terminal restoration.