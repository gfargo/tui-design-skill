**In a list, `/` should focus the filter box and narrow the visible rows as you type.** Reuse the existing box. In documents or logs, `/` instead searches within content.

The key distinction is who owns text input:

| Context | `/` | `Space` | `Tab` |
|---|---|---|---|
| List has focus | Focus filter | Toggle current row’s mark | Move focus |
| Separate filter box has focus | Insert `/` | Insert a space | Move focus |
| Always-typing picker, like fzf | Insert `/` | Insert a space | Toggle mark and move down |

For an always-typing picker, `Shift+Tab` toggles and moves up. Reserve Tab for marking throughout that picker; don’t also use it to cycle focus. Printable shortcuts such as `q`, `j`, and `?` must remain text while the box owns input.

For multi-select, I recommend these rules:

- Keep the **cursor row and marked set separate**. Moving the cursor never changes marks.
- Preserve marks across filtering and sorting, using stable item IDs. Show `5 selected (2 hidden)` when filtering hides marked items.
- Label bulk selection **“Select all matching”** and scope it to filtered results. In a text box, preserve `Ctrl+A` for text editing.
- Bulk actions operate on all marked items, including hidden ones; disclose the total before destructive actions.
- `Esc` clears the filter first, then clears marks on a subsequent press. It never quits. Closing a popup takes priority.

Show the result count, highlight matching text, and update within roughly 100 ms. No matches should display `No matches` while retaining the query and marks.

For a single-list view, keep the layout compact:

```text
Wide                                      60-column split
Filter: api_           12/240              Filter: api_   12/240
> * api-server                            > * api-server
    api-worker                                api-worker
5 selected (2 hidden)                     5 selected (2 hidden)
Space mark  / filter  Enter open          Space mark  / filter  Enter open
```

Here `>` means cursor and `*` means marked. Use zero borders, no repeated unmarked-row glyphs, and one cue per state. At 80×24 and 60 columns, preserve the filter, list, counts, and controls; truncate long labels and hide optional columns. Below a declared minimum such as 40×6, show a truthful “terminal too small” message.