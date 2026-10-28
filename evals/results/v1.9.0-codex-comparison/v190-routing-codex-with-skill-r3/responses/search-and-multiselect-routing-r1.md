**In a list, `/` should filter: narrow the visible rows as the user types.** In documents or logs, `/` instead searches within content, with `n` / `N` moving between matches.

Choose multi-select bindings according to who owns text input:

| Context | `/` | Space | Tab |
|---|---|---|---|
| List has navigation focus | Focus/open filter | Toggle current row’s mark | Move focus |
| Filter box owns input | Insert literal `/` | Insert a space | Move focus |
| Dedicated type-to-filter picker | Insert literal `/` | Insert a space | Toggle mark, then move down |

For the dedicated picker, `Shift+Tab` toggles and moves up; Tab no longer cycles focus. **Use that override only when the picker is a self-contained interaction.** For a list beside other controls, retain normal focus traversal and let users focus the list to mark with Space.

Keep these behaviors explicit:

- **Cursor and marks are separate.** Arrows move the cursor; marking identifies the batch action’s targets. Track both by stable item IDs.
- **Preserve marks across filtering.** Show `3 marked (2 hidden)` so an action cannot silently include unseen items. Label select-all as “Select all matching” if that is its scope.
- **Text entry wins.** `j`, `q`, `?`, and action letters enter text while the filter owns input.
- **Esc clears the filter first**, returning focus to the list; a subsequent Esc clears marks. Each press performs one step; Esc never quits.
- Update results promptly, show `visible/total`, and display `No matches — Esc clear filter` when empty.

For an ordinary list, the layout can stay small:

```text
Wide / 80x24                         60-column split
Filter: api_       12/240             Filter: api_   12/240
> * api-east       Running            > * api-east
    api-west       Stopped                api-west
3 marked (2 hidden)                   3 marked (2 hidden)
Space mark  / filter  Tab focus       Space mark  / filter  Tab focus
```

At 60 columns, drop secondary columns and truncate names while preserving the filter, marks, count, and controls. Use zero nested borders, `>` only for the cursor, and `*` only for marked rows; two control/status rows carry the necessary chrome. Below the size needed for those rows plus one result, show a clear “terminal too small” message.