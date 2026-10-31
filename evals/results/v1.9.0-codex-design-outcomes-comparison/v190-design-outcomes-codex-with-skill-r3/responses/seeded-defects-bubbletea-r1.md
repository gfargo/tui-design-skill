I would hold the merge. The main blockers are blocking network I/O, false success reporting, and unbounded rendering.

This is a browsable CI dashboard: a full-screen list with detail on Enter fits the workflow. The snippet uses Bubble Tea v1 APIs; the recommendations below retain that version.

1. **Refreshing freezes the UI.**  
   `http.Get` and JSON decoding run inside `Update`. During a slow request, keys, resize events, and even `q` cannot be processed. The default HTTP client also has no overall timeout.

   **Fix:** return a `tea.Cmd` that fetches and decodes into a local slice, then returns a result message. Only `Update` installs the result. Use a configured client with a timeout and a cancellable request. Ignore repeated `r` while loading, or cancel superseded requests and reject obsolete results.

2. **Failed responses can appear successful and damage existing data.**  
   HTTP 4xx/5xx responses do not make `http.Get` return an error. The decode error is ignored, and `m.ok = true` runs regardless. Decoding directly into `m.rows` can also partially modify its contents before failing.

   **Fix:** check the HTTP status, check decoding and schema validation, and replace `m.rows` only after complete success. Bound response size and support pagination if the API requires it. Keep the previous successful rows on failure and label them stale. Closing the body is already correct; move that responsibility into the command.

3. **The layout ignores the actual terminal size.**  
   The 80-character rule wraps in a 60-column pane. Rendering every row can push the status off-screen, and there is no scrolling.

   **Fix:** handle `tea.WindowSizeMsg`, store width and height, and reserve space for the header and footer. Render only the visible row slice using a Bubbles table/list or an explicit viewport offset. Recompute geometry on resize, clamp dimensions before allocating, and show a small placeholder before the initial size arrives.

4. **Neither field is safely constrained to its column.**  
   `%-20s` sets a minimum width, not a maximum. Long names overflow; Go formatting measures runes rather than terminal cells. Long `Detail` strings wrap, while embedded newlines create extra rows.

   **Fix:** sanitize display text, truncate each table cell by terminal width, then pad by measured cell width. Use a grapheme-aware width/truncation library such as `charmbracelet/x/ansi`, with `lipgloss.Width` for measurement. Keep table rows single-line; show full detail in a wrapped, scrollable detail view.

   Treat both API fields as untrusted terminal content: remove terminal escape sequences and handle control characters explicitly. An ANSI-aware width function does **not** sanitize text.

5. **`ok` conflates several different states.**  
   The initial screen shows a red dot despite no request having failed. There is no loading indication, empty state, error explanation, or freshness information. Green indicates a successful fetch, which users could mistake for passing pipelines.

   **Fix:** track loading, the last error, whether data has ever loaded, and the last successful refresh time. Render explicit text such as:

   - `Loading pipelines…`
   - `No pipelines found · r refresh`
   - `Refresh failed: timeout · showing previous results · r retry`

   Start the initial fetch from `Init`, or explicitly show “Press r to load.” Keep fetch status distinct from pipeline status.

6. **Selection and navigation are unfinished.**  
   `cursor` is unused. Users cannot select a row, scroll, or inspect truncated detail.

   **Fix:** implement Up/Down, Page Up/Page Down, Enter for detail, and Esc to return. Show concise controls in the footer. Track selection by a stable API ID across refreshes; an index alone can silently select a different pipeline after reordering. Handle removal and empty results without indexing invalid rows.

7. **Status depends entirely on color.**  
   The same `●` means success or failure solely through red/green. That meaning disappears in monochrome, and the glyph can have ambiguous width.

   **Fix:** use status words, semantic styles, and optional color reinforcement. Honor `NO_COLOR` and offer ASCII output. A text status makes the dot unnecessary.

For pane sizing, I would use one list pane at both 80 and 60 columns, with full details available on Enter. Schematic layouts:

```text
80 columns                               60 columns
Pipelines · updated 12:04                 Pipelines · updated 12:04
  NAME                 DETAIL              NAME             DETAIL
> deploy-main          Waiting for...     > deploy-main      Waiting...
  test-api             Integration...      test-api         Integrat...

1/42 · ↑↓ move · Enter detail             1/42 · ↑↓ move · Enter detail
r refresh · q quit                       r refresh · q quit
```

At 80×24, reserve four lines for header, column labels, and controls, leaving 20 visible rows. At 60 columns, shrink the name column and truncate summaries more aggressively. At a proposed minimum of 40×8, hide the summary column and retain names plus detail drill-down. Below that, show a bounded “Need 40×8; resize or q” state while keeping quit operational.

The clutter audit is small but concrete: border nesting is zero; the decorative rule consumes an entire line without conveying data; the dot uses one signal whose meaning is undocumented. Remove both and spend that space on status and controls. Exact chrome percentage depends on row count and detail wrapping, but those elements currently consume two lines regardless of useful content.

Finally, verify the surrounding startup code, which is absent here: use framework-managed alternate-screen cleanup for this full-screen dashboard, keep diagnostics away from its display, and provide linear plain/JSON output for non-TTY use.

Before merging, test delayed requests with responsive quit/resize, HTTP errors and malformed JSON preserving old rows, empty results, selection across reordered refreshes, and large datasets. Pin rendered frames at 80×24, 60×12, and the minimum, including CJK, combining characters, long multiline details, escape sequences, and monochrome output.