`/` should focus the filter box from the list. Once the box has focus, typing—including spaces—edits the query. Show a hint such as **`/ Filter`**.

Keep filtering and selection separate:

- **↑/↓:** move the active row.
- **Space:** toggle selection when the list has focus.
- **Shift+↑/↓:** extend a selection range across visible rows.
- **Tab:** move between the filter and list; preserve the query and selections.
- **Esc:** return from the filter to the list without clearing the query. Provide an explicit clear-filter control.

Selections should survive filtering. Show **“5 selected · 2 hidden by filter”** so bulk actions have a predictable scope. “Select all” should select the filtered results, and its label should say so.

The key rule: **Space types in the filter; Space selects in the list.** Make keyboard focus visually obvious.