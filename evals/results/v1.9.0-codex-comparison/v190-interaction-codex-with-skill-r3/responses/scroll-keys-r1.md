Use **arrows plus familiar navigation aliases**, with a **right-aligned item count** such as `42/1,203`.

| Keys | Action |
|---|---|
| `↑` / `↓`, `k` / `j` | Move selection one row |
| `PgUp` / `PgDn` | Move one page, retaining one row of overlap |
| `Ctrl+U` / `Ctrl+D` | Move half a page |
| `Home` / `End`, `gg` / `G` | Jump to first / last item |
| Mouse wheel | Scroll the viewport under the pointer without changing selection |

Enable printable aliases only when a text field isn’t accepting input. Keep the selection three rows from the viewport edge while moving; reduce that margin to one row when fewer than 12 rows are visible.

The indicator should mean **selected item / total items in the current list**. After filtering, use the filtered total; show the original total separately if useful. For an empty list, show `0 items`. A scrollbar is optional; the numeric count should remain.

```text
Wide                                      60-column split
Items                         42/1,203    Items             42/1,203
  Previous item                             Previous item
> Selected item                           > Selected item
  Next item                                 Next item

Up/Down move  PgUp/PgDn page  ? help       Up/Down move  ? help
```

At 80×24 and 60 columns, preserve the list and count, truncate long labels, and shorten hints before sacrificing data rows. Keep all bindings available through help.

For this layout, use zero borders, one selection marker, and two chrome rows—title and hints. Omit repeated row bullets, a duplicate percentage, and a default scrollbar. Below the width needed for a recognizable item label plus the count, show a clear “terminal too small” message.