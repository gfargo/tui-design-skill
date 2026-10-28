**In a list, `/` should activate filtering:** narrow the visible rows as the user types. In documents or logs, `/` instead searches within content, with `n`/`N` for next/previous match.

If your list already has a filter box, `/` should focus that existing box. Once the box owns input, `/`, Space, `j`, `k`, and `q` are literal query characters.

Choose multi-select bindings by interaction style:

| Context | Marking | Navigation / focus |
|---|---|---|
| List has focus; filter box is a separate field | **Space** toggles current row | Arrows move; Tab cycles focus |
| Type-to-filter picker; query stays active while browsing | **Tab** toggles and moves down; **Shift+Tab** toggles and moves up | Arrows move; Tab no longer cycles focus |

For a dedicated picker, I recommend the second pattern. For a list inside a larger application, use the first so Tab remains predictable between panels.

Keep **cursor position and marked items separate**:

- Track marks by stable item ID. Filtering and sorting preserve them.
- Show a `*` on marked rows and `>` on the current row; both survive monochrome.
- Report hidden selections: `3 marked (1 hidden)`. Actions apply to all marked items, so confirmations must include hidden ones.
- Define “Select all” as **all matching rows**, label that scope, and provide a visible alternative to `Ctrl+A`, which also means line-start in text input.
- Make Esc unwind one step: leave filter editing, clear an applied filter, then clear marks on a later press. Never clear everything or quit with one Esc.

A compact picker could look like this:

```text
Wide                                       60-column split
Filter: api_     12/240                     Filter: api_  12/240
>* api-server       production             >* api-server
 * api-worker       staging                 * api-worker
   api-gateway      production                api-gateway
3 marked (1 hidden)                        3 marked (1 hidden)
Tab mark  Enter choose  Esc cancel         Tab mark  Enter choose  Esc cancel
```

At 80×24, keep optional metadata; at 60 columns, drop it and truncate long names while preserving the query, counts, and controls. This needs no borders, no repeated unmarked glyphs, and only two fixed chrome rows plus the footer. If those controls and at least one result cannot fit, show a clear “terminal too small” state.