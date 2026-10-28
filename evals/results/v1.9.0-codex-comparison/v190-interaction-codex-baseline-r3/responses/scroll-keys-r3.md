For a terminal list view, I’d use these defaults:

| Key | Action |
|---|---|
| `↑` / `↓` | Move selection one item; scroll when needed |
| `Page Up` / `Page Down` | Move one viewport, keeping one row of overlap |
| `Home` / `End` | Jump to the first / last item |
| `j` / `k` | Optional aliases for down / up, outside text inputs |
| Mouse wheel | Scroll a few rows |

Keep selection visible and stop at the ends rather than wrapping.

Put a compact position indicator at the bottom right:

- **Selectable list:** `23 of 140` for the selected item.
- **Scroll-only list:** `21–40 of 140` for the visible range.
- **Unknown total:** `21–40 · more below`; avoid a misleading percentage.

For long lists, add a slim scrollbar showing the viewport’s relative size and position. Hide the indicator when everything fits unless the item count is useful.