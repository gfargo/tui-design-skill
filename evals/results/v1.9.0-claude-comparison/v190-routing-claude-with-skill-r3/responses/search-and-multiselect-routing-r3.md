**Short answer:** in a list, `/` should filter (narrow the rows shown), not search. Multi-select works through two input states. While the filter box has focus, **Tab** marks a row. Once the list has focus again, **Space** marks a row. Marks stay on items even when the filter hides them.

## What `/` does

`/` is the conventional key for both search and filter, and the focused view decides which one it means. Documents and logs search with it. Lists filter with it, the way k9s and fzf do.

- Pressing `/` opens or focuses the filter box. The list narrows as each key is typed, and an update slower than about 100 ms feels broken.
- Show the match count (`23/1,204`) and highlight the matched part of each row.
- Use smart-case: an all-lowercase query ignores case, and a query with any capital letter matches case exactly.
- **Enter** keeps the filter and moves focus back to the list. **Esc** clears the filter.
- Track the cursor by item ID, not row position. When the filter changes, the cursor stays on the same item if it's still visible. If it's not, it goes to the nearest remaining item, not to the top.

## Multi-select alongside the filter box

The conflict: Space is the usual mark key, but while a text box has focus, Space is just part of the query.

| Focus | Printable keys | Mark | Move |
|---|---|---|---|
| **Filter box** (after `/`) | go into the query | **Tab** marks and moves down; **Shift+Tab** marks and moves up (fzf `--multi`) | `↑`/`↓`, `Ctrl+J`/`Ctrl+K` (not `j`/`k`, which are letters here) |
| **List** (after Enter, or no filter) | are commands | **Space** toggles | `↑`/`↓`, `j`/`k` |

- Tab normally switches focus between panels. While the filter box has focus, Tab marks rows instead, and the footer hint should say so.
- **Marks belong to items, not to the current filter.** You can filter `foo`, mark three rows, change the query to `bar`, and mark two more. Show the total including hidden marks: `5 marked (2 hidden)`. Otherwise a bulk delete can hit rows the user can't see.
- Show marked rows with a `*` prefix and an accent background. The `*` keeps the mark visible without color.
- Action keys (`d`, `y`, Enter) apply to all marked rows if any exist, and to the cursor row otherwise. Before a destructive action, highlight exactly which rows it will affect and confirm with the count: `Delete 5 items? [y/N]`.
- Optional extras: select all (`Ctrl+A` is taken by GNU screen and readline, so also give it a printable key) and invert (`*`).

## Esc and q

Each Esc press undoes one thing, innermost first, and Esc never quits:

1. Clear the query, if there is one.
2. Clear the marks. If any are hidden by the filter, say so: `cleared 5 marks`.
3. Go back a level, if the list is nested.

While the filter box has focus, `q` is just a letter.

## Layout

Wide (≈100 columns):
```
 / foo▏                                         23/1,204 · 5 marked (2 hidden)
 * foo-api        running   3d   10.0.4.12   us-east-1
   foo-worker     pending   2m   10.0.4.19   us-east-1
 * foo-cache      running   9d   10.0.4.30   us-west-2
 ─────────────────────────────────────────────────────────────────────────────
 Tab mark  ↑↓ move  Enter apply filter  Esc clear  ? help
```

At the 60-column floor, the list keeps its width. Columns drop from the right, and the counter shortens:
```
 / foo▏                       23/1204 · 5✱
 * foo-api        running   3d
   foo-worker     pending   2m
 ──────────────────────────────────────────
 Tab mark  Enter apply  Esc clear  ? help
```
The footer hints change with focus. In list mode they read `Space mark  / filter  d delete…`.

If this view is really a summon–choose–exit picker rather than a long-lived list, drop list mode and let the query always have focus, fzf-style. Then Tab is the only mark key and Enter returns the marked items.
