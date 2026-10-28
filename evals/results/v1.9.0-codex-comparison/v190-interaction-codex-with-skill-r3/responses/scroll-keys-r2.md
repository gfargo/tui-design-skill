Use **arrows plus familiar navigation aliases**, and show **`42/1,203`** right-aligned in the list’s header or footer.

| Keys | Behavior |
|---|---|
| `↑` / `↓`, `k` / `j` | Move selection one row |
| `PgUp` / `PgDn` | Move one viewport, retaining one row of overlap |
| `Ctrl+U` / `Ctrl+D` | Move half a viewport |
| `Home` / `End` | Jump to first / last item |
| `g` / `G` | Optional top / bottom aliases; use `gg` for top if your app follows Vim conventions |
| Mouse wheel | Scroll the viewport under the pointer without changing selection |

Printable aliases must yield while a search or text field owns input.

Keep **three rows of context** between the moving selection and the viewport edge; reduce this to **one row when the viewport is under 12 rows tall**. Clamp movement at the first and last items.

The position indicator means **selected item / total items in the current list**. Use `0/0` for an empty list. A scrollbar is optional; keep the numeric indicator even if you add one.

A compact, borderless layout works at both widths:

```text
Wide (80 columns)                  Narrow (60 columns)
Items                  42/1,203    Items            42/1,203
  Previous item                      Previous item
> Selected item                    > Selected item
  Next item                          Next item
Up/Down move  PgUp/PgDn page  ?     Up/Down move  ? help
```

At 80×24, keep page hints visible; at 60 columns, shorten hints and truncate item labels while preserving the count. Put the complete keymap in `?` help.

Clutter budget: **zero borders, one selection cue, two chrome rows**. Skip repeated row markers and a redundant percentage. If even one item plus the header and hints cannot fit, show a truthful “terminal too small” message.