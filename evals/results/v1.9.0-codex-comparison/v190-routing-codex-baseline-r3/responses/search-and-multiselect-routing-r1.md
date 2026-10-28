Use `/` to **focus the filter box**. Keep selection separate from filtering:

- **Typing in the filter box** updates the visible list. Space enters a space; standard text shortcuts apply.
- **↑/↓** moves the active row. From the filter box, ↓ moves focus into the results.
- **Space on a row** toggles its selection and keeps focus there.
- **Shift+↑/↓** extends selection across visible rows.
- **Ctrl/Cmd+A in the list** selects all filtered results; in the filter box, it selects text.
- **Esc** moves focus from the filter back to the list. It shouldn’t silently clear selection.

Preserve selections when filtering hides them, and show **“5 selected · 2 hidden by filter.”** Bulk actions should clearly apply to all selected items, including hidden ones, with a visible **Clear selection** action.

If typing anywhere in the list already starts filtering, `/` is a convenient explicit shortcut. Only intercept it outside the text box, so users can still type `/` into a query.