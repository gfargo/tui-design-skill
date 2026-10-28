`/` should **focus the filter box**, preserving the current query and selecting its text so the user can replace it immediately. Treat `/` as a shortcut only when focus is outside a text field.

Keep filtering and selection separate:

| Focus | Behavior |
|---|---|
| Filter box | Typing edits the query; Space inserts a space; ↓ moves into results |
| List | ↑/↓ moves the active row; Space toggles its selection; Shift+↑/↓ extends selection |
| Either | Esc clears a nonempty filter first; otherwise returns focus to the list |

For multi-select:

- Keep selections when filtering hides selected items.
- Show both counts: **“5 selected · 2 hidden by filter.”**
- Make **Select all** apply to filtered results, and label it accordingly.
- Provide an explicit **Clear selection** action.
- Apply bulk actions to all selected items, including hidden ones, with the total visible before execution.

If typing anywhere in the list automatically starts filtering, printable characters—including Space—must go to the filter. In that model, use a dedicated selection shortcut, such as Ctrl+Space. My preference is explicit `/` to filter and Space to select: it keeps both interactions predictable.