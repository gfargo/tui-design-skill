For a selectable TUI list, use familiar navigation keys and a **right-aligned `42/1,203` indicator** showing the selected item’s position and total.

| Keys | Behavior |
|---|---|
| `↑` / `↓`, `k` / `j` | Move selection one row |
| `PgUp` / `PgDn` | Move one viewport, with one row of overlap |
| `Ctrl+U` / `Ctrl+D` | Move half a viewport |
| `Home` / `End` | Jump to first / last item |
| `gg` / `G` | Optional Vim aliases for first / last |
| Mouse wheel | Scroll the viewport under the pointer without changing selection |

Keep **three rows of context** above or below the moving selection when possible; reduce that to one when the viewport has fewer than 12 rows. Stop at the ends rather than wrapping.

Printable aliases should yield to text entry. In a type-to-filter picker, typing `j`, `k`, or `g` must enter those characters.

Use the count consistently:

- `42/1,203`: selected item within the current list.
- When filtered, use the filtered total; show the original total separately if useful.
- Empty list: `0/0` with “No items” or “No matches.”
- Unknown total: `42/?` rather than an invented percentage.

A scrollbar is optional. The numeric count should remain readable without color.

At wide and 60-column widths, keep the same structure:

```text
Wide
Items                                                          42/1,203
  Previous item
> Selected item
  Next item
Up/Down move | PgUp/PgDn page | / filter | ? help

60 columns
Items                                               42/1,203
  Previous item
> Selected item with a long name truncated...
  Next item
Up/Down move | PgUp/PgDn page | / filter | ? help
```

At 80×24 and in a 60-column split, preserve the count and list, truncate long labels, and put extra aliases in `?` help. Below the space needed for a header, one item, and hints, show a “Terminal too small” message with working exit keys.

Clutter budget: zero enclosing borders, one selection marker, one position count, and two chrome rows. Skip repeated row numbers, a percentage beside the count, and nested boxes.